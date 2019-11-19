# coding: utf-8
import json
import time
import traceback
import logging
from ..service import (
    GlobalizationService
)
from ..key import (
    REDIS_VOICE_ANOY_CHECK_POOL,
    REDIS_ANOY_CHECK_POOL,
    REDIS_VIDEO_ANOY_CHECK_POOL,
    REDIS_HUANXIN_ONLINE,
    REDIS_ONLINE_GENDER_REGION,
    REDIS_ONLINE_REGION,
    REDIS_ANOY_GENDER_ONLINE_REGION,
    REDIS_VOICE_GENDER_ONLINE_REGION,
    REDIS_VIDEO_GENDER_ONLINE_REGION,
    REDIS_ACCELERATE_REGION_TYPE_GENDER,
    REDIS_FEED_SQUARE_REGION,
    REDIS_FEED_HQ_REGION,
)
from ..const import (
    GENDERS,
    ONE_DAY,
    ONE_MIN,
    ONE_HOUR
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class MaintainService(object):
    JUDGE_CNT = 10000
    ONLINE_SET_CLEAR = 3 * ONE_DAY
    '''
    维护系统运行的各种定时任务
    '''

    @classmethod
    def clean_anoy_check(cls):
        for k in [REDIS_VIDEO_ANOY_CHECK_POOL, REDIS_VOICE_ANOY_CHECK_POOL, REDIS_ANOY_CHECK_POOL]:
            cnt = redis_client.zcard(k)
            if cnt < cls.JUDGE_CNT/100:
                continue
            redis_client.zremrangebyscore(k, 0, int(time.time()) - ONE_DAY)

    @classmethod
    def clear_huanxin(cls):
        redis_client.zremrangebyscore(REDIS_HUANXIN_ONLINE, 0, int(time.time()) - cls.ONLINE_SET_CLEAR)

    @classmethod
    def clear_online(cls):
        for r in GlobalizationService.REGIONS:
            online_key = REDIS_ONLINE_REGION.format(region=r)
            if redis_client.zcard(online_key) > cls.JUDGE_CNT:
                redis_client.zremrangebyscore(online_key, 0, int(time.time()) - cls.ONLINE_SET_CLEAR)
            for g in GENDERS:
                online_gender_key = REDIS_ONLINE_GENDER_REGION.format(region=r, gender=g)
                if redis_client.zcard(online_gender_key) > cls.JUDGE_CNT:
                    redis_client.zremrangebyscore(online_gender_key, 0, int(time.time()) - cls.ONLINE_SET_CLEAR)

    @classmethod
    def clear_suqare(cls):
        for r in GlobalizationService.REGIONS:
            for k in [REDIS_FEED_HQ_REGION, REDIS_FEED_SQUARE_REGION]:
                key = k.format(region=r)
                if redis_client.zcard(key) > cls.JUDGE_CNT:
                    redis_client.zremrangebyscore(key, 0, int(time.time()) - 7 * ONE_DAY)

    @classmethod
    def help_anoy_online(cls):
        for r in GlobalizationService.REGIONS:
            for k in [REDIS_ANOY_GENDER_ONLINE_REGION, REDIS_VOICE_GENDER_ONLINE_REGION, REDIS_VIDEO_GENDER_ONLINE_REGION, REDIS_ACCELERATE_REGION_TYPE_GENDER]:
                for g in GENDERS:
                    key = k.format(region=r, gender=g)
                    if redis_client.zcard(key) > cls.JUDGE_CNT:
                        redis_client.zremrangebyscore(key, 0, int(time.time()) - ONE_DAY)


    @classmethod
    def clear_sortedset_by_region(cls, region):
        cls.clean_anoy_check()
        cls.help_anoy_online()
        cls.clear_huanxin()
        cls.clear_online()
        cls.clear_suqare()

