import os
import sys
import fcntl
from hendrix.conf import setting
from litatom.service import StatisticService
import time

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
        StatisticService.refresh_online_cnts()
        time.sleep(1)

if __name__ == "__main__":
    run()

