# coding: utf-8
import json
import time
import traceback
import logging
from ..key import (
    REDIS_SHARE_STAT
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class ShareStatService(object):
    '''
    '''

    @classmethod
    def _get_key(cls, user_id):
        return REDIS_SHARE_STAT.format(user_id=user_id)

    @classmethod
    def add_stat_item(cls, user_id, item):
        redis_client.sadd(cls._get_key(user_id), item)
        return True

    @classmethod
    def get_stat_item_num(cls, user_id):
        num = redis_client.scard(cls._get_key(user_id))
        return num

    @classmethod
    def get_stat_items(cls, user_id):
        return redis_client.sscan(cls._get_key(user_id))[1]
