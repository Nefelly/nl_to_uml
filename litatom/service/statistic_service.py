# coding: utf-8
import time
import random
from ..redis import RedisClient
# from ..key import (
#     REDIS_ONLINE_GENDER,
#     REDIS_ONLINE_GENDER_REGION,
#     REDIS_ONLINE,
#     REDIS_ONLINE_REGION
# )
from flask import request
from ..const import (
    GENDERS,
    GIRL,
    BOY,
    MAX_TIME,
    USER_ACTIVE,
    REAL_ACTIVE,
    FIVE_MINS
)
from ..service import (
    UserService,
    GlobalizationService,
    UserFilterService
)
from ..model import (
    User,
    TrackChat,
    UserSetting,
    OnlineLimit
)
redis_client = RedisClient()['lit']

class StatisticService(object):
    MAX_SELECT_POOL = 1000

    @classmethod
    def get_online_cnt(cls, gender=None):
        judge_time = int(time.time()) - USER_ACTIVE
        if gender:
            # key = REDIS_ONLINE_GENDER.format(gender=gender)
            key = GlobalizationService._online_key_by_region_gender(gender)
            return redis_client.zcount(key, judge_time, MAX_TIME)
        res = 0
        for _ in GENDERS:
            # key = REDIS_ONLINE_GENDER.format(gender=_)
            key = GlobalizationService._online_key_by_region_gender(_)
            res += redis_client.zcount(key, judge_time, MAX_TIME)
        return res

    @classmethod
    def _user_infos_by_uids(cls, uids):
        user_infos = []
        if uids:
            all_online = UserService.uid_online(uids[-1]) == True   # last user online
            all_not_online = UserService.uid_online(uids[0]) == False   # first user not online
            for uid in uids:
                _ = UserService.get_basic_info(User.get_by_id(uid))
                if not _:
                    continue
                if all_online:
                    online = True
                elif all_not_online:
                    online = False
                else:
                    online = UserService.uid_online(uid)
                _['online'] = online
                user_infos.append(_)
        return user_infos

    @classmethod
    def choose_first_frame(cls, user_id, key, gender, num):
        '''
        第一页的好友 特殊处理, 先从在线列表取人;再随机, 再根据年龄排序 再返回
        :param gender:
        :param num:
        :return:
        '''
        # online_cnt = cls.get_online_cnt(gender)
        judge_time = int(time.time()) - REAL_ACTIVE
        key = GlobalizationService._online_key_by_region_gender(gender)
        online_cnt = redis_client.zcount(key, judge_time, MAX_TIME)
        choose_pool = num
        if online_cnt > num:
            choose_pool = min(online_cnt, cls.MAX_SELECT_POOL)
        uids = redis_client.zrevrange(key, 0, choose_pool)
        uids = random.sample(uids, min(2 * num, len(uids)))
        age = User.age_by_user_id(user_id)

        uid_agediffs = []
        for uid in uids:
            age_diff = abs(age - User.age_by_user_id(uid))
            uid_agediffs.append([uid, age_diff])
        res = sorted(uid_agediffs, key=lambda el: el[1])
        uids = [el[0] for el in res][:num]
        return uids

    @classmethod
    def online_users_by_interval(cls, gender, interval, user_id=None):
        #GlobalizationService.set_current_region_for_script(GlobalizationService.REGION_TH)
        key = GlobalizationService._online_key_by_region_gender(gender)
        time_now = int(time.time())
        raw_uids = redis_client.zrangebyscore(key, time_now - interval, time_now)
        return raw_uids

    @classmethod
    def get_online_users(cls, gender=None, start_p=0, num=10):
        key = GlobalizationService._online_key_by_region_gender(gender)
        online_cnt = cls.get_online_cnt(gender)
        has_next = False
        next_start = -1
        if False and start_p == 0 and request.user_id and gender and online_cnt >= num:
            uids = cls.choose_first_frame(request.user_id, key, gender, num)
            has_next = (len(uids) == num)
        else:
            girl_strategy_on = False
            if gender == BOY and start_p == 0 and girl_strategy_on:
                '''girls has to have some girl'''
                b_ratio = 0.3
                girl_num = int(num * b_ratio)
                num = boy_num = int(num)   # set num to this for next get
                girl_start_p = int(start_p * b_ratio) + 1
                girl_uids = redis_client.zrevrange(GlobalizationService._online_key_by_region_gender(GIRL), girl_start_p, girl_start_p + girl_num)
                boy_uids = redis_client.zrevrange(GlobalizationService._online_key_by_region_gender(BOY), start_p, start_p + boy_num)
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
            if gender == BOY and girl_strategy_on:
                if len(boy_uids) == num + 1:
                    has_next = True
                    boy_uids = boy_uids[:-1]
                uids = boy_uids[:-1] + girl_uids
                random.shuffle(uids)
            else:
                if len(uids) == num + 1:
                    has_next = True
                    uids = uids[:-1]
        if temp_uid:
            # uids = [el for el in uids if UserFilterService.filter_by_age_gender(temp_uid, el)]
            uids = []
            user_setting = UserSetting.get_by_user_id(temp_uid)
            max_loop_tms = 5
            if user_setting and user_setting.online_limit:
                for i in range(max_loop_tms):
                    temp_uids = redis_client.zrevrange(key, start_p, start_p + num)
                    has_next = False
                    if len(temp_uids) == num + 1:
                        has_next = True
                        temp_uids = temp_uids[:-1]
                    next_start = start_p + num if has_next else -1
                    uids += [el for el in temp_uids if UserFilterService.filter_by_age_gender(temp_uid, el)]
                    if len(uids) >= max(num - 3, 1) or not has_next:
                        break
                    start_p = start_p + num
            else:
                if start_p == 0:
                    user_age = User.age_by_user_id(temp_uid)
                    time_now = int(time.time())
                    raw_uids = redis_client.zrangebyscore(key, time_now - FIVE_MINS, time_now)
                    uids = [el for el in raw_uids if abs(User.age_by_user_id(el) - user_age) <= 4]
                    has_next = True
                    next_start = len(raw_uids) + 1
            uids = [el for el in uids if el != temp_uid]
            if not uids:
                uids =  [el for el in redis_client.zrevrange(key, start_p, start_p + num) if el != temp_uid]
                has_next = len(uids) == num + 1
                next_start = start_p + num if has_next else -1
        user_infos = cls._user_infos_by_uids(uids)
        return {
            'has_next': has_next,
            'user_infos': user_infos,
            'next_start': next_start
        }

    # @classmethod
    # def get_online_users(cls, gender=None, start_p=0, num=10):
    #     key = GlobalizationService._online_key_by_region_gender(gender)
    #     online_cnt = cls.get_online_cnt(gender)
    #     has_next = False
    #     next_start = -1
    #     if False and start_p == 0 and request.user_id and gender and online_cnt >= num:
    #         uids = cls.choose_first_frame(request.user_id, key, gender, num)
    #         has_next = (len(uids) == num)
    #     else:
    #         girl_strategy_on = False
    #         if gender == BOY and start_p == 0 and girl_strategy_on:
    #             '''girls has to have some girl'''
    #             b_ratio = 0.3
    #             girl_num = int(num * b_ratio)
    #             num = boy_num = int(num)   # set num to this for next get
    #             girl_start_p = int(start_p * b_ratio) + 1
    #             girl_uids = redis_client.zrevrange(GlobalizationService._online_key_by_region_gender(GIRL), girl_start_p, girl_start_p + girl_num)
    #             boy_uids = redis_client.zrevrange(GlobalizationService._online_key_by_region_gender(BOY), start_p, start_p + boy_num)
    #             uids = girl_uids + boy_uids
    #         else:
    #             uids = []
    #             max_loop_tms = 5
    #             temp_uid = request.user_id
    #             if temp_uid:
    #                 for i in range(max_loop_tms):
    #                     temp_uids = redis_client.zrevrange(key, start_p, start_p + num)
    #                     has_next = False
    #                     if len(temp_uids) == num + 1:
    #                         has_next = True
    #                         temp_uids = temp_uids[:-1]
    #                     next_start = start_p + num if has_next else -1
    #                     uids += [el for el in temp_uids if UserFilterService.filter_by_age_gender(temp_uid, el)]
    #                     if len(uids) >= max(num - 3, 1) or not has_next:
    #                         break
    #                     start_p = start_p + num
    #             else:
    #                 uids = redis_client.zrevrange(key, start_p, start_p + num)
    #         temp_uid = request.user_id
    #         if temp_uid and temp_uid in uids:
    #             temp_num = num + 1
    #             uids = redis_client.zrevrange(key, start_p, start_p + temp_num)
    #             uids = [uid for uid in uids if uid != temp_uid]
    #         uids = uids if uids else []
    #         has_next = False
    #         if gender == BOY and girl_strategy_on:
    #             if len(boy_uids) == num + 1:
    #                 has_next = True
    #                 boy_uids = boy_uids[:-1]
    #             uids = boy_uids[:-1] + girl_uids
    #             random.shuffle(uids)
    #         # else:
    #         #     if len(uids) == num + 1:
    #         #         has_next = True
    #         #         uids = uids[:-1]
    #     user_infos = cls._user_infos_by_uids(uids)
    #     return {
    #         'has_next': has_next,
    #         'user_infos': user_infos,
    #         'next_start': next_start
    #     }

    @classmethod
    def track_chat(cls, user_id, target_user_id, content):
        track = TrackChat()
        track.uid = user_id
        track.target_uid = target_user_id
        track.content = content
        track.create_ts = int(time.time())
        track.save()
        return {"track_id": str(track.id)}, True
