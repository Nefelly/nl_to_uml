# coding: utf-8
import json
import time
import traceback
import logging
from ..service import (
    GlobalizationService
)
from ..key import (
    REDIS_ANOY_GENDER_ONLINE,
    REDIS_VOICE_ANOY_CHECK_POOL,
    REDIS_HUANXIN_ONLINE,
    REDIS_ONLINE_GENDER_REGION,
    REDIS_ONLINE_REGION,
    REDIS_ANOY_GENDER_ONLINE_REGION,
    REDIS_ANOY_CHECK_POOL,
    REDIS_FEED_SQUARE_REGION,
    REDIS_FEED_HQ_REGION,
    REDIS_VOICE_GENDER_ONLINE_REGION,
    REDIS_VIDEO_ANOY_CHECK_POOL,
    REDIS_VIDEO_GENDER_ONLINE_REGION
)
from ..const import (
    GENDERS
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class MaintainService(object):
    '''
    维护系统运行的各种定时任务
    '''

    @classmethod
    def clear_sortedset_by_region(cls, region):
        pass

