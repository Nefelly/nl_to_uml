import os
import time
from litatom.service import AnoyMatchService, VoiceMatchService


if __name__ == "__main__":
    print "started at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    AnoyMatchService.clean_pools()
    VoiceMatchService.clean_pools()
    print "ended at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
