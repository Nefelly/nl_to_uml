# coding: utf-8
import time
from ..redis import RedisClient
from ..key import (
    REDIS_ONLINE_GENDER
)
from ..const import (
    ONLINE_LIVE,
    GENDERS,
    GIRL,
    MAX_TIME
)
from ..service import UserService
from ..model import User
redis_client = RedisClient()['lit']

class StatisticService(object):

    @classmethod
    def get_online_cnt(cls, gender=None):
        judge_time = int(time.time()) - ONLINE_LIVE
        if gender:
            key = REDIS_ONLINE_GENDER.format(gender=gender)
            return redis_client.zcount(key, judge_time, MAX_TIME)
        res = 0
        for _ in GENDERS:
            key = REDIS_ONLINE_GENDER.format(gender=_)
            res += redis_client.zcount(key, judge_time, MAX_TIME)
        return res

    @classmethod
    def uid_online(cls, uid, key):
        '''
        :return uid: online map
        :param uids:
        :return:
        '''
        judge_time = int(time.time()) - ONLINE_LIVE
        score = redis_client.zscore(key, uid)
        if not score or int(score) < judge_time:
            return False
        return True

    @classmethod
    def get_online_users(cls, gender=None, start_p=0, num=10):
        if gender:
            key = REDIS_ONLINE_GENDER.format(gender=gender)
            uids = redis_client.zrevrange(key, start_p, start_p + num)
            uids = uids if uids else []
            has_next = False
            if len(uids) == num + 1:
                has_next = True
                uids = uids[:-1]
            user_infos = []
            all_online = cls.uid_online(key, uids[-1]) == True   # last user online
            all_not_online = cls.uid_online(key, uids[0]) == False   # first user not online
            for uid in uids:
                _ = UserService.get_basic_info(User.get_by_id(uid))
                if all_online:
                    online = True
                elif all_not_online:
                    online = False
                else:
                    online = cls.uid_online(uid, key)
                _['online'] = online
                user_infos.append(_)
            user_infos = map(UserService.get_basic_info, map(User.get_by_id, uids))
            for el in user_infos:
                el['online'] = True
            return {
                'has_next': has_next,
                'user_infos': user_infos,
                'next_start': start_p + num if has_next else -1
            }
        else:
            res = {}
            for gender in GENDERS:
                res[gender] = cls.get_online_users(gender, start_p, num)
            return res