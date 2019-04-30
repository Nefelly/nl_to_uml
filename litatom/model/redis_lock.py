# coding: utf-8
import logging
from ..key import REDIS_LOCK
from ..redis import RedisClient




logger = logging.getLogger(__name__)
redis_client = RedisClient()['lit']

class RedisLock(object):
    """
    redis锁,用来防止并发刷新, 多次获取红包等
    """
    EXPIRE_TIME = 5
    @classmethod
    def get_mutex(cls, key):
        try:
            redis_key = REDIS_LOCK.format(key=key)
            succ = redis_client.setnx(redis_key, 1)
            redis_client.expire(redis_key, cls.EXPIRE_TIME)
            return succ
        except Exception as e:
            logger.error(str(e))
            return True

    @classmethod
    def release_mutex(cls, key):
        try:
            redis_key = REDIS_LOCK.format(key=key)
            succ = redis_client.delete(redis_key)
            return succ
        except Exception as e:
            logger.error(str(e))
            return True