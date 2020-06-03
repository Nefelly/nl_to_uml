import os
import sys
import fcntl
from hendrix.conf import setting
from litatom.service import ExperimentAnalysisService
from litatom.util import (
    get_zero_today,
    next_date
)
import time


def foo():
    print time.time()
    today = get_zero_today()
    date_str = next_date(today, -1).strftime('%Y-%m-%d')
    ExperimentAnalysisService.cal_all_result(date_str)
    print time.time()

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

