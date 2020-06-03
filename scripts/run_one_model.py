import os
import sys
import fcntl
from hendrix.conf import setting
from litatom.service import AliLogService
import time


def foo():
    start = time.time()
    print start
    AliLogService.get_loglst('"get_fakeid" and "experiment_name"', '20200412', '20200428', 'litatom', 'litatomstore',
                             save_add='/data/alilog/exp1.txt')
    print 'using:', time.time() - start

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
    foo()

if __name__ == "__main__":
    run()

