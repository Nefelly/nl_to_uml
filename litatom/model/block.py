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
    REDIS_BLOCK_CACHE
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
    def get_redis_key(cls, uid):
        return REDIS_BLOCK_CACHE.format(user_id=uid)

    @classmethod
    def in_block(cls, uid, blocked):
        """
        判断blocked是否被uid所屏蔽
        :param uid:
        :param blocked:
        :param blocked_num:
        :return:
        """
        key = cls.get_redis_key(uid)
        # 缓存保护，屏蔽个数太多将不再缓存，以下以被block个数作为临界
        # if blocked_num > cls.BLOCK_NUM_THRESHOLD - cls.PROTECT:  # PROTECT 用来保护缓存不会因为like num 一上一下不断刷缓存
        #     if blocked_num >= cls.BLOCK_NUM_THRESHOLD:
        #         redis_client.delete(key)
        #     obj = cls.objects(uid=uid, blocked=blocked).first()
        #     return True if obj else False
        cls.ensure_cache(uid)
        return redis_client.sismember(key, blocked)

    @classmethod
    def ensure_cache(cls, uid):
        """
        对uid已屏蔽的user_id进行缓存
        :param uid:
        :return:
        """
        key = cls.get_redis_key(uid)
        if not redis_client.exists(key):
            blockeds = [e.blocked for e in cls.objects(uid=uid)]
            if blockeds:
                redis_client.sadd(key, *blockeds)
                redis_client.expire(key, cls.CACHED_TIME)

    @classmethod
    def block(cls, uid, blocked):
        if uid == blocked:
            return False
        return False
        cls.ensure_cache(uid)
        key = cls.get_redis_key(uid)
        obj = cls(uid=uid, blocked=blocked)
        if not obj:
            obj.save()
        redis_client.sadd(key, blocked)
        # if not cls.get_by_block(uid, blocked):
        #     obj = cls(uid=uid, blocked=blocked)
        #     obj.save()
        return True

    @classmethod
    def unblock(cls, uid, blocked):
        key = cls.get_redis_key(uid)
        if not redis_client.exists(key):
            return False
        redis_client.srem(key, blocked)
        obj = cls.get_by_block(uid, blocked)
        if obj:
            obj.delete()
            obj.save()
        return True

    # obj = cls.get_by_block(uid, blocked)
    # if obj:
    #     obj.delete()
    #     obj.save()
    #     return True
    # return False

    @classmethod
    def reverse(cls, uid, blocked):
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
            res = True
        else:
            obj.delete()
            res = False
        key = cls.get_redis_key(uid)
        if redis_client.exists(key):
            if res:
                redis_client.sadd(key, blocked)
            else:
                redis_client.srem(key, blocked)
        else:
            if res:
                cls.ensure_cache(uid)
                redis_client.sadd(key, blocked)
        return res
        # if cls.BLOCK_NUM_THRESHOLD > blocked_num:
        #     key = cls.get_redis_key(blocked)
        #     if cls.LIKE_NUM_THRESHOLD - cls.PROTECT <= blocked_num:
        #         if redis_client.exists(key):
        #             if blocked:
        #                 redis_client.sadd(key, uid)
        #             else:
        #                 redis_client.srem(key, uid)
        #     else:
        #         cls.ensure_cache(blocked)
        #         if blocked:
        #             redis_client.sadd(key, uid)
        #         else:
        #             redis_client.srem(key, uid)
        # return blocked
