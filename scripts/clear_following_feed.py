import os
import time
from litatom.service import (
    MaintainService
)
import sys
import fcntl
from hendrix.conf import setting
import time


def foo():
    print "started at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    MaintainService.clear_following_feed()
    print "ended at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

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
