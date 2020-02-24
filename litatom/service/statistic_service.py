# coding: utf-8
import time
import random
import datetime
from ..redis import RedisClient
from ..key import (
    REDIS_ONLINE_CNT_CACHE
)
from flask import request
from ..const import (
    GENDERS,
    GIRL,
    BOY,
    MAX_TIME,
    USER_ACTIVE,
    REAL_ACTIVE,
    FIVE_MINS,
    ONE_MIN
)
from ..service import (
    UserService,
    GlobalizationService,
    UserFilterService,
    AliLogService
)
from ..model import (
    User,
    TrackChat,
    UserSetting,
    OnlineLimit,
    UserAccount
)

redis_client = RedisClient()['lit']


class StatisticService(object):
    MAX_SELECT_POOL = 1000

    @classmethod
    def online_cnt_cache_key(cls, region, gender=None):
        gender = 'NSET' if gender == None else gender
        return REDIS_ONLINE_CNT_CACHE.format(region=region, gender=gender)

    @classmethod
    def refresh_online_cnts(cls):
        judge_time = int(time.time()) - USER_ACTIVE
        for r in GlobalizationService.REGIONS:
            t_cnt = 0
            for g in GENDERS:
                key = GlobalizationService._online_key_by_region_gender(g, r)
                num = redis_client.zcount(key, judge_time, MAX_TIME)
                redis_client.set(cls.online_cnt_cache_key(r, g), num, ex=ONE_MIN)
                t_cnt += num
            redis_client.set(cls.online_cnt_cache_key(r), t_cnt, ex=ONE_MIN)

    @classmethod
    def get_online_cnt(cls, gender=None):
        cache_res = redis_client.get(cls.online_cnt_cache_key(GlobalizationService.get_region(), gender))
        if cache_res:
            return int(cache_res)
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
            all_online = UserService.uid_online(uids[-1]) == True  # last user online
            all_not_online = UserService.uid_online(uids[0]) == False  # first user not online
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
        # GlobalizationService.set_current_region_for_script(GlobalizationService.REGION_TH)
        key = GlobalizationService._online_key_by_region_gender(gender)
        time_now = int(time.time())
        raw_uids = redis_client.zrangebyscore(key, time_now - interval, time_now, 0, cls.MAX_SELECT_POOL)
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
                num = boy_num = int(num)  # set num to this for next get
                girl_start_p = int(start_p * b_ratio) + 1
                girl_uids = redis_client.zrevrange(GlobalizationService._online_key_by_region_gender(GIRL),
                                                   girl_start_p, girl_start_p + girl_num)
                boy_uids = redis_client.zrevrange(GlobalizationService._online_key_by_region_gender(BOY), start_p,
                                                  start_p + boy_num)
                uids = girl_uids + boy_uids
            # else:
            #     uids = redis_client.zrevrange(key, start_p, start_p + num)
            # temp_uid = request.user_id
            # if temp_uid and temp_uid in uids:
            #     temp_num = num + 1
            #     uids = redis_client.zrevrange(key, start_p, start_p + temp_num)
            #     uids = [uid for uid in uids if uid != temp_uid]
            # uids = uids if uids else []
            # has_next = False
            # if gender == BOY and girl_strategy_on:
            #     if len(boy_uids) == num + 1:
            #         has_next = True
            #         boy_uids = boy_uids[:-1]
            #     uids = boy_uids[:-1] + girl_uids
            #     random.shuffle(uids)
            # else:
            #     if len(uids) == num + 1:
            #         has_next = True
            #         uids = uids[:-1]
        temp_uid = request.user_id
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
                for i in range(max_loop_tms):
                    temp_uids = redis_client.zrevrange(key, start_p, start_p + num)
                    has_next = False
                    if len(temp_uids) == num + 1:
                        has_next = True
                        temp_uids = temp_uids[:-1]
                    user_age = User.age_by_user_id(temp_uid)
                    next_start = start_p + num if has_next else - 1
                    uids += [el for el in temp_uids if abs(User.age_by_user_id(el) - user_age) <= 4]
                    if len(uids) >= max(num - 3, 1) or not has_next:
                        break
                    start_p = start_p + num
                # if start_p == 0:
                #     user_age = User.age_by_user_id(temp_uid)
                #     time_now = int(time.time())
                #     raw_uids = redis_client.zrangebyscore(key, time_now - ONE_MIN, time_now, 0, cls.MAX_SELECT_POOL)
                #     uids = [el for el in raw_uids if abs(User.age_by_user_id(el) - user_age) <= 4]
                #     has_next = True
                #     next_start = len(raw_uids) + 1
            uids = [el for el in uids if el != temp_uid]
            if not uids:
                uids = [el for el in redis_client.zrevrange(key, start_p, start_p + num) if el != temp_uid]
                has_next = len(uids) == num + 1
                next_start = start_p + num if has_next else -1
        else:
            uids = redis_client.zrevrange(key, start_p, start_p + num)
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


class DiamStatService(object):
    STAT_QUERY_LIST = {
        'diam_cons_num': 'diamonds<0 |SELECT -sum(diamonds) as res',
        'diam_cons_people_num': 'diamonds<0 |SELECT COUNT(DISTINCT user_id) as res',
        'diam_deposit_num': 'name:deposit|SELECT sum(diamonds) as res',
        'diam_deposit_people_num': 'name:deposit|SELECT COUNT(DISTINCT user_id) as res',
        'diam_deposit50_people_num': 'name:deposit and diamonds=50|SELECT COUNT(DISTINCT user_id) as res',
        'diam_deposit100_people_num': 'name:deposit and diamonds=100|SELECT COUNT(DISTINCT user_id) as res',
        'diam_deposit200_people_num': 'name:deposit and diamonds=200|SELECT COUNT(DISTINCT user_id) as res',
        'diam_deposit500_people_num': 'name:deposit and diamonds=500|SELECT COUNT(DISTINCT user_id) as res',
        'week_member_consumer_num': 'name:week_member |SELECT COUNT(DISTINCT user_id) as res',
        'week_member_diam_cons_num': 'name:week_member |SELECT -sum(diamonds) as res',
        'acce_consumer_num': 'name:accelerate | SELECT count(DISTINCT user_id) as res',
        'acce_diam_cons_num': 'name:accelerate | SELECT -sum(diamonds) as res',
    }
    FREE_QUERY_LIST = {
        'diam_incr_num': 'diamonds>0|select sum(diamonds) as res',
    }
    MATCH_QUERY_LIST = {
        'text_match_num': 'action:match and remark:matchSuccesstext|SELECT COUNT(1) as res,user_id GROUP BY user_id limit 1000000',
        'video_match_num': 'action:match and remark:matchSuccessvideo|SELECT COUNT(1) as res, user_id GROUP BY user_id limit 1000000',
        'voice_match_num': 'action:match and remark:matchSuccessvoice|SELECT COUNT(1) as res, user_id GROUP BY user_id limit 1000000'
    }
    DEFAULT_PROJECT = 'litatom-account'
    DEFAULT_LOGSTORE = 'account_flow'
    USER_MEM_TIME = {}  # user_id:membership_time

    @classmethod
    def _load_user_account(cls):
        """预装载函数，从UserAccount表中抽取会员的user_id, membership_time；之后可视情况只抽取一天的会员信息"""
        members = UserAccount.objects(membership_time__ne=0)
        for member in members:
            cls.USER_MEM_TIME[member.user_id] = member.membership_time

    @classmethod
    def fetch_log(cls, from_time, to_time, query, size=-1, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE):
        """
        :return: 如果size要求在400000一下，或者全部，则返回一个GetLogResponse对象；如果超过，则返回一个GetLogResponse迭代器
        注意，如果size==-1,则要求总条数不得超过1000000
        """
        if size < 400000:
            return AliLogService.get_log_atom(project=project, logstore=logstore, from_time=from_time, to_time=to_time)
        else:
            return AliLogService.get_log_by_time_and_topic(project=project, logstore=logstore, from_time=from_time,
                                                           to_time=to_time, query=query)

    @classmethod
    def cal_mem_num(cls, to_time, from_time):
        """计算会员总数"""
        res = 0
        for id in cls.USER_MEM_TIME:
            if from_time <= cls.USER_MEM_TIME[id] < to_time:
                res += 1
        return res

    @classmethod
    def cal_match_num(cls, from_time, to_time, from_timestamp, to_timestamp, query):
        """
        计算匹配过程中钻石与会员等数量统计
        :return: 一个字典，key为1-12,>12，value为一个元组，(匹配成功key次的人数，未使用钻石非会员人数，未使用钻石会员人数，使用钻石会员人数)
        """
        resp = cls.fetch_log(from_time, to_time, project='liatomaction', logstore='liatomactionstore', query=query)
        match_num = {}
        for i in range(12):
            match_num[str(i + 1)] = (0, 0, 0, 0)
        match_num['>12'] = (0, 0, 0, 0)
        for log in resp.logs:
            contents = log.get_contents()
            # 匹配成功次数
            res = contents['res']
            if res not in match_num:
                res = '>12'
            match_num[res][0] += 1
            # 该用户当日是否使用过钻石
            user_id = contents['user_id']
            resp = cls.fetch_log(from_time, to_time, query='user_id:' + user_id + ' and diamonds<0', size=2)
            if resp.get_count() > 1:
                match_num[res][3] += 1
                continue
            # 该用户未使用钻石，是会员
            if user_id in cls.USER_MEM_TIME:
                if from_timestamp <= cls.USER_MEM_TIME[user_id] <= to_timestamp:
                    match_num[res][2] += 1
                    continue
            # 该用户未使用钻石，不是会员
            match_num[res][1] += 1
        return match_num

    @classmethod
    def cal_all_match_num(cls, from_time, to_time, from_timestamp, to_timestamp):
        for name in cls.MATCH_QUERY_LIST:
            contents = []
            match_num = cls.cal_match_num(from_time, to_time, from_timestamp, to_timestamp, cls.MATCH_QUERY_LIST[name])
            for key in match_num:
                contents.append(('match_num ' + key, str(match_num[key][0])))
                contents.append(('match_num ' + key + '/no_mem_no_diam', str(match_num[key][1])))
                contents.append(('match_num ' + key + '/is_mem_no_diam', str(match_num[key][2])))
                contents.append(('match_num' + key + '/is_mem_is_diam', str(match_num[key][3])))
            AliLogService.put_logs(contents, topic=name, project='litatom-account', logstore='diamond_match')

    @classmethod
    def cal_stats_from_list(cls, list, from_time, to_time):
        data = []
        for item in list:
            resp = cls.fetch_log(from_time=from_time, to_time=to_time, query=list[item])
            for log in resp.logs:
                contents = log.get_contents()
                try:
                    res = contents['res']
                except KeyError:
                    res = 0
                finally:
                    data.append((item, str(res)))
        return data

    @classmethod
    def diam_stat_report(cls, date):
        yesterday = date + datetime.timedelta(days=-1)
        time_today = time.mktime(date.timetuple())
        time_yesterday = time.mktime(yesterday.timetuple())
        from_time = AliLogService.datetime_to_alitime(yesterday)
        to_time = AliLogService.datetime_to_alitime(date)
        data = []

        mem_num = cls.cal_mem_num(time_today, time_yesterday)
        data.append(('member_num', str(mem_num)))
        data += cls.cal_stats_from_list(cls.STAT_QUERY_LIST, from_time, to_time)
        AliLogService.put_logs(data, project='litatom-account', logstore='diamond_stat')

    @classmethod
    def diam_free_report(cls, date):
        yesterday = date + datetime.timedelta(days=-1)
        time_today = time.mktime(date.timetuple())
        time_yesterday = time.mktime(yesterday.timetuple())
        from_time = AliLogService.datetime_to_alitime(yesterday)
        to_time = AliLogService.datetime_to_alitime(date)
        data = []
        data += cls.cal_stats_from_list(cls.FREE_QUERY_LIST, from_time, to_time)
        AliLogService.put_logs(project='litatom-account', logstore='diamond_match', contents=data,
                               topic='diamonds_incr')
        cls.cal_all_match_num(from_time, to_time, time_yesterday, time_today)

    @classmethod
    def diam_report(cls, date=datetime.datetime.now()):
        cls._load_user_account()
        cls.diam_stat_report(date)
        cls.diam_free_report(date)
