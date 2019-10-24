# coding: utf-8
import random
import logging
import json
from hendrix.conf import setting
from ..redis import RedisClient
from ..util import (
    now_date_key
)
from ..key import (
    REDIS_AD_TIMES_LEFT
)
from ..const import (
    ONE_DAY
)
redis_client = RedisClient()['lit']

logger = logging.getLogger(__name__)

class AdService(object):
    """
    广告服务
    """
    MAX_TIMES = 5 if not setting.IS_DEV else 30

    @classmethod
    def times_left(cls, user_id):
        now_date = now_date_key()
        match_left_key = REDIS_AD_TIMES_LEFT.format(user_date=user_id + now_date)
        redis_client.setnx(match_left_key, cls.MAX_TIMES)
        redis_client.expire(match_left_key, ONE_DAY)
        times_left = int(redis_client.get(match_left_key))
        if times_left <= 0:
            return u'You have reached the maximum number of times you can watch video today', False
        return {
                   'times_left': times_left,
        }, True

    @classmethod
    def decr_times_left(cls, user_id):
        now_date = now_date_key()
        match_left_key = REDIS_AD_TIMES_LEFT.format(user_date=user_id + now_date)
        if not redis_client.get(match_left_key):
            redis_client.setnx(match_left_key, cls.MAX_TIMES)
            redis_client.expire(match_left_key, ONE_DAY)
        redis_client.decr(match_left_key)

    @classmethod
    def verify_ad_viewed(cls, user_id, payload):
        cls.decr_times_left(user_id)
        return True
