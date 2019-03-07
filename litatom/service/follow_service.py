# coding: utf-8
from ..redis import RedisClient

class FollowService(object):

    @classmethod
    def feed_num(cls, user_id):
        return 3

    @classmethod
    def follow_eachother(cls, uid1, uid2):
        pass