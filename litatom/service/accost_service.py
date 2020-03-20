# coding: utf-8
import logging
from ..redis import RedisClient
from ..key import (
    REDIS_ACCOST_RATE,
    REDIS_ACCOST_STOP_RATE
)
from ..const import (
    ONE_MIN,
    ACTION_ACCOST_STOP,
    ACTION_ACCOST_NEED_VIDEO
)
from ..service import (
    TrackActionService,
    AliLogService,
)

logger = logging.getLogger(__name__)
redis_client = RedisClient()['lit']


class AccostService(object):
    '''
    docs :https://developer.qiniu.com/censor/api/5588/image-censor
    '''
    ACCOST_PASS = 'pass'
    ACCOST_BAN = 'ban'
    ACCOST_NEED_VIDEO = 'need_video'
    ACCOST_INTER = 5 * ONE_MIN
    ACCOST_RATE = 5
    ACCOST_STOP_INTER = 10 * ONE_MIN
    ACCOST_STOP_RATE = 19

    @classmethod
    def can_accost(cls, user_id, session_id, loc, version):
        def should_stop():
            stop_key = REDIS_ACCOST_STOP_RATE.format(user_id=user_id)
            stop_num = redis_client.get(stop_key)
            if not stop_num:
                redis_client.set(stop_key, cls.ACCOST_STOP_RATE - 1, cls.ACCOST_STOP_INTER)
                return False
            else:
                stop_num = int(stop_num)
                if stop_num <= 0:
                    TrackActionService.create_action(user_id, ACTION_ACCOST_STOP)
                    return True
                redis_client.decr(stop_key)
                return False
        print(0)
        key = REDIS_ACCOST_RATE.format(user_id=user_id)
        rate = cls.ACCOST_RATE - 1  # the first time is used
        res = redis_client.get(key)
        if not res:
            if should_stop():
                return cls.ACCOST_BAN
            redis_client.set(key, rate, cls.ACCOST_INTER)
            print(1)
            cls.record_accost(user_id, session_id, loc, version)
            return cls.ACCOST_PASS
        else:
            res = int(res)
            if res <= 0:
                TrackActionService.create_action(user_id, ACTION_ACCOST_NEED_VIDEO)
                return cls.ACCOST_NEED_VIDEO
            else:
                if should_stop():
                    return cls.ACCOST_BAN
                redis_client.decr(key)
                print(2)
                cls.record_accost(user_id, session_id, loc, version)
                return cls.ACCOST_PASS

    @classmethod
    def reset_accost(cls, user_id, data=None):
        key = REDIS_ACCOST_RATE.format(user_id=user_id)
        redis_client.set(key, cls.ACCOST_RATE, cls.ACCOST_INTER)
        return None, True

    @classmethod
    def record_accost(cls, user_id, session_id, loc, version):
        contents = [('action', 'accost'),('location',loc),('remark', 'accost_pass'),('session_id', str(session_id)),
                    ('user_id', str(user_id)),('version',version)]
        print(contents)
        AliLogService.put_logs(contents)
