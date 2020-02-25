# coding: utf-8
import json
import time
import traceback
import logging
from ..key import (
    REDIS_SHARE_STAT,
    REDIS_SHARE_KNOWN_NUM,
)
from ..service import (
    AccountService
)
from ..const import (
    ONE_WEEK,
    ONE_MONTH,
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']


class ShareStatService(object):
    """
    分享链接领钻石相关服务
    """
    CACHED_TIME = ONE_WEEK
    CACHED_RECORD_TIME = ONE_MONTH
    ERR_SHARE_NOT_ENOUGH = 'not enough shared members'

    @classmethod
    def _get_key(cls, user_id):
        return REDIS_SHARE_STAT.format(user_id=user_id)

    @classmethod
    def _get_known_num_key(cls, user_id):
        return REDIS_SHARE_KNOWN_NUM.format(user_id=user_id)

    @classmethod
    def ensure_cache(cls, user_id):
        known_key = cls._get_known_num_key(user_id)
        if not redis_client.exists(known_key):
            redis_client.set(known_key, 0)
        redis_client.expire(known_key, cls.CACHED_RECORD_TIME)
        key = cls._get_key(user_id)
        if redis_client.exists(key):
            redis_client.expire(key, cls.CACHED_TIME)

    @classmethod
    def add_stat_item(cls, user_id, item):
        key = cls._get_key(user_id)
        redis_client.sadd(key, item)
        redis_client.expire(key, cls.CACHED_TIME)
        return True

    @classmethod
    def get_stat_item_num(cls, user_id):
        """返回历史上为该用户点击分享链接的所有用户人数"""
        num = redis_client.scard(cls._get_key(user_id))
        return num

    @classmethod
    def get_known_num(cls, user_id):
        """返回该用户已经领奖过的分享人数"""
        cls.ensure_cache(user_id)
        return int(redis_client.get(cls._get_known_num_key(user_id)))

    @classmethod
    def get_shown_num(cls, user_id):
        """返回显示给用户的x/5中的x"""
        total_num = cls.get_stat_item_num(user_id)
        if not total_num:
            return 0
        known_num = cls.get_known_num(user_id)
        return total_num - known_num

    @classmethod
    def get_stat_items(cls, user_id):
        return redis_client.sscan(cls._get_key(user_id))[1]

    @classmethod
    def claim_rewards(cls, user_id):
        """
        集满5人点击分享链接，兑换100钻石奖励
        :return: 返回两项，第一项是错误信息，无则为None, 第二项是是否钻石变动成功
        """
        if cls.get_shown_num(user_id) < 5:
            return cls.ERR_SHARE_NOT_ENOUGH, False
        key = cls._get_known_num_key(user_id)
        redis_client.set(key, cls.get_stat_item_num(user_id))
        return AccountService.deposit_by_activity(user_id,AccountService.SHARE_5)


