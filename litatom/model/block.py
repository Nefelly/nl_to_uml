# coding: utf-8
import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from ..const import (
    ONE_MIN
)
from ..redis import RedisClient
from ..key import (
    REDIS_BLOCKED_CACHE
)

redis_client = RedisClient()['lit']


class Blocked(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    BLOCK_NUM_THRESHOLD = 500
    PROTECT = 5
    CACHED_TIME = 50 * ONE_MIN
    uid = StringField(required=True)
    blocked = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_block(cls, uid, blocked):
        return cls.objects(uid=uid, blocked=blocked).first()

    @classmethod
    def get_redis_key(cls, blocked):
        return REDIS_BLOCKED_CACHE.format(blocked=blocked)

    @classmethod
    def in_block(cls, uid, blocked, blocked_num):
        """
        判断blocked是否被uid所屏蔽
        :param uid:
        :param blocked:
        :param blocked_num:
        :return:
        """
        key = cls.get_redis_key(blocked)
        if blocked_num > cls.BLOCK_NUM_THRESHOLD - cls.PROTECT:  # PROTECT 用来保护缓存不会因为like num 一上一下不断刷缓存
            if blocked_num >= cls.BLOCK_NUM_THRESHOLD:
                redis_client.delete(key)
            obj = cls.objects(uid=uid, blocked=blocked).first()
            return True if obj else False
        cls.ensure_cache(blocked)
        return redis_client.sismember(key, uid)

    @classmethod
    def ensure_cache(cls, blocked):
        """
        对被block的一部分feed进行缓存
        :param blocked:
        :return:
        """
        key = cls.get_redis_key(blocked)
        if not redis_client.exists(key):
            uids = [e.uid for e in cls.objects(blocked=blocked)]
            if uids:
                redis_client.sadd(key, *uids)
                redis_client.expire(key, cls.CACHED_TIME)

    @classmethod
    def block(cls, uid, blocked):
        if uid == blocked:
            return False
        if not cls.get_by_block(uid, blocked):
            obj = cls(uid=uid, blocked=blocked)
            obj.save()
        return True

    @classmethod
    def unblock(cls, uid, blocked):
        obj = cls.get_by_block(uid, blocked)
        if obj:
            obj.delete()
            obj.save()
            return True
        return False

    @classmethod
    def reverse(cls, uid, blocked, blocked_num):
        """
        返回最终是否是block
        :param blocked_num:
        :param uid:
        :param blocked:
        :return:
        """
        obj = cls.get_by_block(uid, blocked)
        if not obj:
            obj = cls(uid=uid, blocked=blocked)
            obj.save()
            blocked = True
        else:
            obj.delete()
            blocked = False
        if cls.BLOCK_NUM_THRESHOLD > blocked_num:
            key = cls.get_redis_key(blocked)
            if cls.LIKE_NUM_THRESHOLD - cls.PROTECT <= blocked_num:
                if redis_client.exists(key):
                    if blocked:
                        redis_client.sadd(key, uid)
                    else:
                        redis_client.srem(key, uid)
            else:
                cls.ensure_cache(blocked)
                if blocked:
                    redis_client.sadd(key, uid)
                else:
                    redis_client.srem(key, uid)
        return blocked
