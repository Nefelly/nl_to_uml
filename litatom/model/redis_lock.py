# coding: utf-8
from ..key import REDIS_LOCK
from ..redis import RedisClient

redis_client = RedisClient()['lit']

class RedisLock(object):
    """
    redis锁,用来防止并发刷新, 多次获取红包等
    """
    EXPIRE_TIME = 5
    @classmethod
    def get_mutex(cls, key):
        redis_key = REDIS_LOCK.format(key=key)
        succ = redis_client.setnx(redis_key, True)
        redis_client.expire(redis_key, cls.EXPIRE_TIME)
        return succ

    @classmethod
    def release_mutex(cls, key):
        redis_key = REDIS_LOCK.format(key=key)
        succ = redis_client.delete(redis_key)
        return succ
