from collections import deque, defaultdict
import logging
import random
import time

from gevent.lock import Semaphore

from .util import Enum
from .metrics import metrics

logger = logging.getLogger(__name__)


class RollingNumber(object):
    _last_idx = 0

    @property
    def now(self):
        return int(time.time() * 1000)

    def __init__(self, window=10 * 1000, interval=1000):
        self.window = window
        self.interval = interval
        self.bucket_num = window / self.interval
        self._new_bucket_lock = Semaphore()

        self.reset(self.now)

    def reset(self, start=None):
        self._buckets = deque([0], maxlen=self.bucket_num)
        self._start = start or self.now

    def get_current_bucket_index(self):
        if not self._new_bucket_lock.acquire(0):
            return self._last_idx

        now = self.now
        elapsed = now - self._start

        if elapsed > self.interval:
            if elapsed > self.window:
                self.reset(now)
                self._new_bucket_lock.release()
                return self._last_idx

            t = elapsed - self.interval
            while t > 0:
                self._buckets.appendleft(0)
                t1, t = t, t - self.interval
                if t < 0:
                    self._start = now - t1
            self._new_bucket_lock.release()
            return self._last_idx

        self._new_bucket_lock.release()
        return self._last_idx

    @property
    def current_bucket_count(self):
        idx = self.get_current_bucket_index()
        return self._buckets[idx]

    def inc(self):
        i = self.get_current_bucket_index()
        self._buckets[i] += 1

    @property
    def sum(self):
        return sum(self._buckets)


class CircuitBreakerError(Exception):
    pass


class CircuitBreaker(object):
    STATE = Enum(
        ('CLOSE', -1),
        ('HALFOPEN', 0),
        ('OPEN', 1),
    )

    e = CircuitBreakerError()

    def __init__(self, window=20 * 1000, interval=1000, max_fail=3,
                 open_time=20 * 1000, half_open_time_ratio=2.0):
        self.error = defaultdict(lambda: RollingNumber(window, interval))
        self.success = defaultdict(lambda: RollingNumber(window, interval))
        self.circuits = {}

        self.max_fail = max_fail
        self.open_time = open_time
        self.half_open_time = self.open_time * half_open_time_ratio
        self._trans_lock = Semaphore()

    def _transition_to_state(self, evt, state):
        if not self._trans_lock.acquire(timeout=0.1):
            return False
        current_state = self.circuits.get(evt, [self.STATE.CLOSE])[0]
        ok = True
        if current_state == state:
            ok = False
        elif current_state == self.STATE.OPEN:
            if state != self.STATE.HALFOPEN:
                ok = False
        elif current_state == self.STATE.CLOSE:
            if state != self.STATE.OPEN:
                ok = False
        if ok:
            now = int(time.time() * 1000)
            self.circuits[evt] = [state, now]
        self._trans_lock.release()
        return ok

    def inc_error(self, evt):
        self.error[evt].inc()
        if self.is_half_open(evt):
            logger.error('error when half open, gonna open: %r', evt)
            self.open(evt)
        elif self.error[evt].sum > self.max_fail:
            logger.error('too much error, gonna open: %r', evt)
            self.open(evt)

    def inc_success(self, evt):
        self.success[evt].inc()
        if self.is_half_open(evt):
            self.close(evt)

    def open(self, evt):
        if self._transition_to_state(evt, self.STATE.OPEN):
            logger.error('circuit breaker open: %r for %dms long', evt,
                         self.open_time)
            metrics['api.circuit_breaker.event'].\
                tags(endpoint=evt, event='open', hostname=metrics.HOSTNAME).\
                commit(1)

    def is_open(self, evt):
        if evt in self.circuits:
            return self.circuits[evt][0] == self.STATE.OPEN
        return False

    def half_open(self, evt):
        ok = self._transition_to_state(evt, self.STATE.HALFOPEN)
        if ok:
            logger.error('circuit breaker half open: %r for %dms long',
                         evt, self.half_open_time - self.open_time)
            metrics['api.circuit_breaker.event'].\
                tags(endpoint=evt, event='halfopen', hostname=metrics.HOSTNAME).\
                commit(1)
        return ok

    def is_half_open(self, evt):
        if evt in self.circuits:
            return self.circuits[evt][0] == self.STATE.HALFOPEN
        return False

    def can_passthrough(self, evt):
        if self.is_close(evt):
            return True
        if self.is_open(evt):
            now = int(time.time() * 1000)
            opened = now - self.circuits[evt][1]
            if opened >= self.open_time:
                if self.half_open(evt):
                    return True
            return False
        if self.is_half_open(evt):
            now = int(time.time() * 1000)
            opened = now - self.circuits[evt][1]
            if opened >= self.half_open_time:
                return True
            t = opened - self.open_time
            return random.randint(0, self.half_open_time - self.open_time) < t
        return False

    def close(self, evt):
        if self._transition_to_state(evt, self.STATE.CLOSE):
            logger.error('circuit breaker closed: %r', evt)
            metrics['api.circuit_breaker.event'].\
                tags(endpoint=evt, event='close', hostname=metrics.HOSTNAME).\
                commit(1)

    def is_close(self, evt):
        if evt in self.circuits:
            return self.circuits[evt][0] == self.STATE.CLOSE
        return True

cb = CircuitBreaker()
