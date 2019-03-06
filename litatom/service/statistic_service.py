# coding: utf-8
from ..redis import RedisClient
from ..key import (
    REDIS_ONLINE_GENDER
)
from ..const import (
    ONLINE_LIVE,
    GENDERS
)
from ..service import UserService
from ..model import User
redis_client = RedisClient()['lit']

class StatisticService(object):
    MAX_TIME = 10 ** 13
    @classmethod
    def feed_num(cls, user_id):
        return 3

    @classmethod
    def get_online_cnt(cls, gender=None):
        judge_time = int(time.time()) - ONLINE_LIVE
        if gender:
            key = REDIS_ONLINE_GENDER.format(gender)
            return redis_client.zcount(key, judge_time, cls.MAX_TIME)
        res = 0
        for _ in GENDERS:
            key = REDIS_ONLINE_GENDER.format(gender)
            res += redis_client.zcount(key, judge_time, cls.MAX_TIME)
        return res

    @classmethod
    def get_online_users(cls, gender, start_p=0, num=10):
        key = REDIS_ONLINE_GENDER.format(gender)
        uids = redis_client.zrevrange(key, start_p, start_p + num)
        uids = uids if uids else []
        has_next = False
        if len(uids) == num + 1:
            has_next = True
            uids = uids[:-1]
        user_infos = map(UserService.get_basic_info, map(User.get_by_id, uids))
        return {
            'has_next': has_next,
            'user_infos': user_infos,
            'next_start': start_p + num if has_next else -1
        }
