import os
import datetime
import time
from litatom.util import ensure_path


def monitor_redis():
    cmd = 'redis-cli -h 127.0.0.1 -p 6379 -a 4567abc info'
    redis_info = os.popen(cmd).read()
    mongo_info = os.popen('mongostat  -u ll -p sgfhgfjty123 --authenticationDatabase admin -n 1 1').read()
    return '\n'.join([redis_info, mongo_info])


def run():
    dst_dir = '/data/log/peak_monitor/'
    addr = os.path.join(dst_dir, 'peak_stat')
    ensure_path(addr)
    f = open(addr, 'w')
    while(True):
        stat_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        info = monitor_redis()
        f.write('%s\n%s\n' % (stat_time, info))
        if datetime.datetime.minute > 10:
            f.close()
            break


if __name__ == "__main__":
    run()
