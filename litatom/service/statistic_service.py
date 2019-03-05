# coding: utf-8
from ..redis import RedisClient

class StatisticService(object):

    @classmethod
    def feed_num(cls, user_id):
        return 3