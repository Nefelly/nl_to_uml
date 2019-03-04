# coding: utf-8
from ..model import RedisClient

class FeedService(object):

    @classmethod
    def feed_num(cls, user_id):
        return 3