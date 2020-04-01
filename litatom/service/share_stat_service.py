# coding: utf-8
import json
import time
import traceback
import logging
from ..key import (
    REDIS_SHARE_STAT,
    REDIS_SHARE_KNOWN_NUM,
    REDIS_CLICK_SHARE,
)
from ..service import (
    AccountService,
    AliLogService
)
from ..const import (
    ONE_WEEK,
    ONE_MONTH,
    ONE_DAY,
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
    CLICK_EXPIRE_TIME = ONE_WEEK
    ERR_SHARE_NOT_ENOUGH = 'not enough shared members'

    @classmethod
    def _get_key(cls, user_id):
        return REDIS_SHARE_STAT.format(user_id=user_id)

    @classmethod
    def _get_known_num_key(cls, user_id):
        return REDIS_SHARE_KNOWN_NUM.format(user_id=user_id)

    @classmethod
    def get_clicker_key(cls, ip):
        return REDIS_CLICK_SHARE.format(ip=ip)

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
    def record_clicker_redis(cls, ip):
        """把点击分享链接的人存入一小时过期的缓存当中，用于估算其是否会因此而下载"""
        max_click = 3
        key = cls.get_clicker_key(ip)
        num = redis_client.incr(key)
        redis_client.expire(key, cls.CLICK_EXPIRE_TIME)
        if num > max_click:
            return False
        return True
        # if not redis_client.exists(ip):
        #     redis_client.set(key, 1)


    @classmethod
    def add_stat_item(cls, user_id, item):
        """有人为user_id 点击share 的链接"""
        key = cls._get_key(user_id)
        if redis_client.sadd(key, item):
            cls.record_clicker_redis(item)
        redis_client.expire(key, cls.CACHED_TIME)
        if not cls.record_click_share_link(item, user_id):
            redis_client.srem(key, item)
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

    @classmethod
    def record_click_share_link(cls, user_ip, target_uid):
        contents = [('action','share'),('remark','click_share_link'),('user_ip',str(user_ip)),
                    ('share_user_id',target_uid)]
        AliLogService.put_logs(contents)


