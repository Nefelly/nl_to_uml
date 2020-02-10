# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    FollowingFeed,
    UserMessage,
    User
)
from ..service import (
    GlobalizationService,
    AnoyMatchService,
    VoiceMatchService,
    VideoMatchService
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
            for g in GENDERS:
                for k in [REDIS_ANOY_GENDER_ONLINE_REGION, REDIS_VOICE_GENDER_ONLINE_REGION, REDIS_VIDEO_GENDER_ONLINE_REGION]:
                    key = k.format(region=r, gender=g)
                    if redis_client.zcard(key) > cls.JUDGE_CNT:
                        redis_client.zremrangebyscore(key, 0, int(time.time()) - ONE_DAY)
                for t in [AnoyMatchService.MATCH_TYPE, VoiceMatchService.MATCH_TYPE, VideoMatchService.MATCH_TYPE]:
                    key = REDIS_ACCELERATE_REGION_TYPE_GENDER.format(match_type=t, region=r, gender=g)
                    if redis_client.zcard(key) > cls.JUDGE_CNT:
                        redis_client.zremrangebyscore(key, 0, int(time.time()) - ONE_DAY)

    @classmethod
    def clear_following_feed(cls):
        maintain_num = 100
        clear_interval = 50
        judge_num = maintain_num + clear_interval
        ids = FollowingFeed.objects().distinct('user_id')
        clear_cnt = 0
        for user in User.objects():
            _ = str(user.id)
            cnt = FollowingFeed.objects(user_id=_).count()
            if cnt > judge_num:
                FollowingFeed.objects(user_id=_).order_by('-feed_create_time').skip(maintain_num).delete()
                clear_cnt += 1
                if clear_cnt % 100 == 0:
                    print clear_cnt

    @classmethod
    def clear_UserMessages(cls):
        keep = 7 * 86400
        judge_time = int(time.time()) - keep
        UserMessage.objects(create_time__lte=judge_time).delete()

    @classmethod
    def clear_sortedset_by_region(cls):
        cls.clean_anoy_check()
        cls.help_anoy_online()
        cls.clear_huanxin()
        cls.clear_online()
        cls.clear_suqare()

