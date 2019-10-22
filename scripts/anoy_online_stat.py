import os
import time, sys
from litatom.const import GENDERS
import fcntl
from hendrix.conf import setting
from litatom.service import AnoyMatchService, VoiceMatchService, VideoMatchService, GlobalizationService
from litatom.model import AnoyOnline
from litatom.redis import RedisClient
from litatom.const import MAX_TIME
from litatom.key import REDIS_VOICE_GENDER_ONLINE_REGION, REDIS_VIDEO_GENDER_ONLINE_REGION, REDIS_ANOY_GENDER_ONLINE_REGION

redis_client = RedisClient()['lit']

def stat():
    regions = GlobalizationService.REGIONS
    types = [REDIS_VOICE_GENDER_ONLINE_REGION, REDIS_VIDEO_GENDER_ONLINE_REGION, REDIS_ANOY_GENDER_ONLINE_REGION]
    while(True):
        for t in types:
            wait_time = {
                REDIS_VOICE_GENDER_ONLINE_REGION: VoiceMatchService.MATCH_WAIT,
                REDIS_VIDEO_GENDER_ONLINE_REGION: VideoMatchService.MATCH_WAIT,
                REDIS_ANOY_GENDER_ONLINE_REGION: AnoyMatchService.MATCH_WAIT
            }.get(t)
            for g in GENDERS:
                for r in regions:
                    ts = int(time.time())
                    key = t.format(gender=g, region=r)
                    judge_time = int(time.time()) - wait_time
                    count = redis_client.zcount(key, judge_time, MAX_TIME)
                    tt = t.split(":")[0]
                    AnoyOnline.create(g, r, tt, ts, count)
                    print g, r, tt, ts, count
        time.sleep(5)

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
    stat()

if __name__ == "__main__":
    run()
