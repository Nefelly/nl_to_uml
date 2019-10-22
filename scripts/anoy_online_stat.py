import os
import time
from litatom.const import GENDERS
from litatom.service import AnoyMatchService, VoiceMatchService, VideoMatchService, GlobalizationService
from litatom.model import AnoyOnline
from litatom.redis import RedisClient
from litatom.user_service import *
from litatom.key import REDIS_VOICE_GENDER_ONLINE_REGION, REDIS_VIDEO_GENDER_ONLINE_REGION, REDIS_ANOY_GENDER_ONLINE_REGION

redis_client = RedisClient()['lit']

def stat():
    regions = GlobalizationService.REGIONS
    types = [REDIS_VOICE_GENDER_ONLINE_REGION, REDIS_VIDEO_GENDER_ONLINE_REGION, REDIS_ANOY_GENDER_ONLINE_REGION]
    while(True):
        for t in types:
            for g in GENDERS:
                for r in regions:
                    ts = int(time.time())
                    key = t.format(gender=g, region=r)
                    count = redis_client.zcount(key)
                    tt = t.split(":")[0]
                    AnoyOnline.create(g, r, tt, ts)
                    time.sleep(1)


if __name__ == "__main__":
    print "started at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    stat()
    print "ended at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
