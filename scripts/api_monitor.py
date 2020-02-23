import sys
import fcntl
from litatom.service import MonitorService

from hendrix.conf import setting

def run():
    mutex_f = '/var/run/%s.mutex' % __file__.split('/')[-1].replace('.py', '')
    if setting.IS_DEV:
        mutex_f += 'dev'
    f = open(mutex_f, 'w')
    try:
        fcntl.flock(f,
                    fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        print 'program already in run'
        sys.exit(0)
    MonitorService.monitor_report()


if __name__ == '__main__':
    run()
