import os
import time
import sys
import fcntl
from litatom.service import UserService
from litatom.redis import RedisClient
from litatom.const import (
    GENDERS,
    USER_ACTIVE
)
from litatom.key import (
    REDIS_ONLINE_GENDER
)
redis_client = RedisClient()['lit']

def refresh_online():
    scan_range = 100
    time_now = int(time.time())
    for g in GENDERS:
        key = REDIS_ONLINE_GENDER.format(gender=g)
        start_scan_time = time_now - USER_ACTIVE - scan_range
        end_scan_time = time_now - USER_ACTIVE + scan_range
        uids = redis_client.zrangebyscore(key, start_scan_time, end_scan_time)
        uid_online_m = UserService.uid_online_by_huanxin(uids)
        for uid, status in uid_online_m.items():
            if status:
                UserService.refresh_status(uid)
                print 'push up:', uid

def run():
    mutex_f = '/var/run/%s.mutex' % __file__.split('/')[-1].replace('.py', '')
    f = open(mutex_f, 'w')
    try:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except:
        print 'program already in run'
        sys.exit(0)
    for i in range(10000):
        refresh_online()
        time.sleep(2)


if __name__ == "__main__":
    run()

