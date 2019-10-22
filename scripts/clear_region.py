import os
import time
from litatom.service import AnoyMatchService, VoiceMatchService, VideoMatchService, GlobalizationService
from litatom.user_service import *


def clear():
    th = [e for e in redis_client.zscan_iter('online:th')]
    id = [e for e in redis_client.zscan_iter('online:id')]
    vn = [e for e in redis_client.zscan_iter('online:vn')]
    o = id + vn
    m = {}
    for k, v in th:
        m[k]= v
    to_clear = [el[0] for el in o if el[0] not in m]


if __name__ == "__main__":
    print "started at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    AnoyMatchService.clean_pools()
    VoiceMatchService.clean_pools()
    VideoMatchService.clean_pools()
    print "ended at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
