# coding: utf-8
import logging
import time
import pickle
from ..redis import RedisClient

from ..key import (
    TOKEN_BUCKET_KEY
)
from ..const import ONE_DAY

redis_client = RedisClient()['lit']


class TokenBucketService(object):
    """
    使用令牌桶算法进行限流, 将数据存储在redis上
    """
    # CAPACITY = 10   # 桶大小
    # RATE = 10    # 速率
    # TIME_INTERVAL = ONE_DAY   # 令牌更新时间间隔
    WHITE_LIST = set(['5b3cc5544eacab7f1b28369f', '5b9b6c5a256a0c0001125678'])

    @classmethod
    def get_token(cls, key, amount=1, rate=1, capacity=1, interval=ONE_DAY, key_live_time=2*ONE_DAY):
        '''

        :param key:
        :param amount: 获取的量
        :param rate: 速率
        :param interval: 时间间隔
        :param capacity: 容量
        :return:
        '''
        if amount < 0:
            return False
        if key in cls.WHITE_LIST:
            return True
        user_key = TOKEN_BUCKET_KEY.format(key=key)
        lst_str = redis_client.get(user_key)
        now = int(time.time())
        if not lst_str:
            tokens = rate
            if tokens >= amount:
                lst_str = pickle.dumps([tokens - amount, now])
                redis_client.set(user_key, lst_str, key_live_time)
                return True
            lst_str = pickle.dumps([tokens, now])
            redis_client.set(user_key, lst_str, key_live_time)
            return False

        tokens, update_t = pickle.loads(lst_str)
        increment = (now - update_t) / interval * rate
        current_token = min(tokens + increment, capacity)
        if current_token < amount:
            if current_token != tokens:
                lst_str = pickle.dumps([current_token, now])
                redis_client.set(user_key, lst_str, key_live_time)
            return False
        current_token -= amount
        lst_str = pickle.dumps([current_token, now])
        redis_client.set(user_key, lst_str, key_live_time)
        return True