import os
import time
from litatom.service import AnoyMatchService


if __name__ == "__main__":
    print "started at", time.strftime("%Y-%m-%d %H:%M:%S", time.local_time(time.time()))
    AnoyMatchService.clean_pools()
    print "ended at", time.strftime("%Y-%m-%d %H:%M:%S", time.local_time(time.time()))
