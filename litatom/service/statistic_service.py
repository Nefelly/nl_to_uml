# coding: utf-8
import time
from ..redis import RedisClient
from ..key import (
    REDIS_ONLINE_GENDER,
    REDIS_ONLINE
)
from flask import request
from ..const import (
    ONLINE_LIVE,
    GENDERS,
    GIRL,
    BOY,
    MAX_TIME,
    USER_ACTIVE
)
from ..service import UserService
from ..model import (
    User,
    TrackChat
)
redis_client = RedisClient()['lit']

class StatisticService(object):

    @classmethod
    def get_online_cnt(cls, gender=None):
        judge_time = int(time.time()) - USER_ACTIVE
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
        judge_time = int(time.time()) - USER_ACTIVE
        score = redis_client.zscore(key, uid)
        if not score or int(score) < judge_time:
            return False
        return True

    @classmethod
    def get_online_users(cls, gender=None, start_p=0, num=10):
        if gender:
            key = REDIS_ONLINE_GENDER.format(gender=gender)
        else:
            key = REDIS_ONLINE

        if gender == BOY and start_p == 0:
            '''girls has to have some girl'''
            b_ratio = 0.5
            girl_num = int(num * b_ratio)
            num = boy_num = int(num)   # set num to this for next get
            girl_start_p = int(start_p * b_ratio) + 1
            girl_uids = redis_client.zrevrange(REDIS_ONLINE_GENDER.format(gender=GIRL), girl_start_p, girl_start_p + girl_num)
            boy_uids = redis_client.zrevrange(REDIS_ONLINE_GENDER.format(gender=BOY), start_p, start_p + boy_num)
            uids = girl_uids + boy_uids
        else:
            uids = redis_client.zrevrange(key, start_p, start_p + num)
        temp_uid = request.user_id
        if temp_uid and temp_uid in uids:
            temp_num = num + 1
            uids = redis_client.zrevrange(key, start_p, start_p + temp_num)
            uids = [uid for uid in uids if uid != temp_uid]
        uids = uids if uids else []
        has_next = False
        if gender == BOY:
            if len(boy_uids) == num + 1:
                has_next = True
                uids = boy_uids[:-1] + girl_uids
        else:
            if len(uids) == num + 1:
                has_next = True
                uids = uids[:-1]
        user_infos = []
        if uids:
            if gender == BOY:
                ''' has to cal onlines on every person'''
                all_online = all_not_online = False
            else:
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

    @classmethod
    def track_chat(cls, user_id, target_user_id, content):
        track = TrackChat()
        track.uid = user_id
        track.target_uid = target_user_id
        track.content = content
        track.create_ts = int(time.time())
        track.save()
        return {"track_id": str(track.id)}, True
