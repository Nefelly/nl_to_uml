import os
import sys
import fcntl
from hendrix.conf import setting
from litatom.service import AliLogService
from litatom.redis import RedisClient
import time


def foo():
    # AliLogService.get_loglst('"get_fakeid" and "experiment_name"', '20200412', '20200428', 'litatom', 'litatomstore',
    #                          save_add='/data/alilog/exp.txt')
    # pass
    redis_client = RedisClient()['lit']
    res = {}
    for _ in redis_client.keys('exp:*'):
        v = redis_client.get(_)
        res[_] = v
    exp = '/tmp/exp'
    default = '/tmp/default'
    exp_keys = [el for el in res if res[el] == 'delay']
    defalut_keys = [el for el in res if res[el] == 'default']
    with open(exp, 'w') as f:
        f.write('/n'.join([el.replace('_match_strategy', '').replace('exp:', '') for el in exp_keys]))
    with open(default, 'w') as f:
        f.write('/n'.join([el.replace('_match_strategy', '').replace('exp:', '') for el in defalut_keys]))

def run():
    mutex_f = '/var/run/%s.mutex' % __file__.split('/')[-1].replace('.py', '')
    if setting.IS_DEV:
        mutex_f += 'dev'
    f = open(mutex_f, 'w')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        print 'program already in run'
        sys.exit(0)
    while (True):
        foo()
        time.sleep(1)

if __name__ == "__main__":
    run()

