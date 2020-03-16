# coding: utf-8
import json
import datetime
import time
import string
import logging
import bson
from collections import Counter
from ..model import *
from ..util import (
    get_zero_today,
    next_date,
    date_to_int_time,
    write_data_to_xls,
    ensure_path,
    now_date_key,
)
from ..service import (
    AliLogService,
)
from mongoengine import (
    DateTimeField,
    IntField,
)

from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class RetainAnaService(object):
    '''
    用户留存数据信息服务
    '''
    IS_TESTING = False

    DAY2BEFORE_ACT = {}
    YESTODAY_ACT = {}


    USER_LOC = {}
    LOC_STATED = ['TH', 'VN']
    CACHED_RES = {}

    COUNTRY_ENCODE = {'VN':1, 'TH':2, 'ID':3}
    GENDER_ENCODE = {'boy':1, 'girl':2}
    ACTION_QUERY=('action:match and remark:startMatch',)

    @classmethod
    def _load_user_action_info(cls, date, user_info, query):
        resp_set = AliLogService.get_log_by_time_and_topic(from_time=AliLogService.datetime_to_alitime(date),
                                                           to_time=AliLogService.datetime_to_alitime(next_date(date,1)),
                                                           project='litatomaction',logstore='litatomactionstore', query=query)
        for resp in resp_set:
            for log in resp.logs:
                contents = log.get_contents()
                user_id = contents['user_id']
                if user_id in user_info.keys():



    @classmethod
    def _load_user_info(cls, date, user_info):
        """
        将指定日期的用户数据load到user_info字典中
        :param date: datetime类型  表示0点
        :param user_info:{user_id1:(loc,gender,age),user_id2:()}
        :return:
        """
        users = User.get_by_crate_time(date_to_int_time(date), date_to_int_time(next_date(date,1)))
        for user in users:
            user_id = user.id
            user_info[user_id] = ()

            loc = user.country
            if loc and loc in cls.COUNTRY_ENCODE:
                user_info[user_id].append(cls.COUNTRY_ENCODE[loc])
            else:
                user_info[user_id].append(0)

            gender = user.gender
            if gender and gender in cls.GENDER_ENCODE:
                user_info[user_id].append(cls.GENDER_ENCODE[gender])
            else:
                user_info[user_id].append(0)

            age = User.age_by_user_id(user_id)
            if age and 13<=age<=25:
                user_info[user_id].append(age)
            else:
                user_info[user_id].append(0)

        for query in cls.ACTION_QUERY:
            cls._load_user_action_info(date, user_info, query)


    @classmethod
    def _get_time_str(cls, table_name, judge_field, days=-1):
        zeroToday = get_zero_today()
        zeroToday = zeroToday + datetime.timedelta(hours=2)
        high_day = next_date(zeroToday, days + 1)
        low_day = next_date(zeroToday, days)
        is_int = isinstance(eval(table_name + '.' + judge_field), IntField)
        low_time = low_day
        high_time = high_day
        if not is_int:
            time_str = "%s__gte=%r, %s__lte=%r" % (judge_field, low_day, judge_field, high_day)
        else:
            low_time = date_to_int_time(low_day)
            high_time = date_to_int_time(high_day)
            time_str = "%s__gte=%r, %s__lte=%r" % (
                judge_field, low_time, judge_field, high_time)
        return time_str, low_time, high_time

    @classmethod
    def load_dicts(cls):
        def get_action(action, remark):
            if action == 'match':
                return '%s_%s' % (action, remark)
            return action
            if len(remark) > 23:
                return action
            return '%s_%s' % (action, remark)
        time_str, low_time, high_time = cls._get_time_str('UserSetting', 'create_time', -2)
        action_time_str, action_low_time, action_high_time = cls._get_time_str('UserAction', 'create_time', -2)
        action_ytime_str, action_ylow_time, action_yhigh_time = cls._get_time_str('UserAction', 'create_time', -1)
        for obj in UserSetting.objects(create_time__gte=low_time, create_time__lte=high_time):
            loc = obj.lang
            user_id = obj.user_id
            cls.USER_LOC[user_id] = loc
            day2_actions = UserAction.objects(user_id=user_id, create_time__gte=action_low_time, create_time__lte=action_high_time)
            cls.DAY2BEFORE_ACT[user_id] = [get_action(action.action, action.remark) for action in day2_actions] if day2_actions else ['None']
            yestoday_acts = UserAction.objects(user_id=user_id, create_time__gte=action_ylow_time, create_time__lte=action_yhigh_time)
            if yestoday_acts:
                cls.YESTODAY_ACT[user_id] = [get_action(action.action, action.remark) for action in yestoday_acts]

    @classmethod
    def get_res(cls, dst_addr):
        def get_res_by_user_ids(user_ids):
            total_acts = 0.0
            act_num = {}
            last_act_num = {}
            for uid in user_ids:
                acts = cls.DAY2BEFORE_ACT[uid]
                total_acts += len(acts)
                last_act = acts[-1]
                if last_act not in last_act_num:
                    last_act_num[last_act] = 1
                else:
                    last_act_num[last_act] += 1
                for act in acts:
                    if act not in act_num:
                        act_num[act] = 1
                    else:
                        act_num[act] += 1
            decimal_num = 4
            total_last = len(user_ids) * 1.0
            for el in act_num:
                act_num[el] = round(act_num[el]/total_last, decimal_num)
                # act_num[el] = round(act_num[el], decimal_num)
            for el in last_act_num:
                last_act_num[el] = round(last_act_num[el]/total_last, decimal_num)
                # last_act_num[el] = round(last_act_num[el], decimal_num)
            return total_acts, act_num, total_last, last_act_num

        cls.load_dicts()
        losing_users = [user_id for user_id in cls.DAY2BEFORE_ACT if user_id not in cls.YESTODAY_ACT]
        retain_users = [user_id for user_id in cls.DAY2BEFORE_ACT if user_id in cls.YESTODAY_ACT]
        totals = get_res_by_user_ids(cls.DAY2BEFORE_ACT.keys())
        retains = get_res_by_user_ids(retain_users)
        losings = get_res_by_user_ids(losing_users)
        actions = totals[1].keys()

        def get_write_line(name, lsts):
            total_acts, act_num, total_last, last_act_num = lsts
            total = [name + '_total', total_acts]
            for el in actions:
                total.append(act_num.get(el, 0))
            last = [name + '_last', total_last]
            for el in actions:
                last.append(last_act_num.get(el, 0))
            return [total, last]
        print actions
        tb_head = ['name', u'总数'] + actions
        res = []
        res += get_write_line('total', totals)
        res += get_write_line('retain', retains)
        res += get_write_line('losing', losings)
        # print res
        for i in range(min(100, len(losing_users))):
            user_id = losing_users[i]
            lst = [user_id] + cls.DAY2BEFORE_ACT.get(user_id, [])[-254:]
            res.append(lst)
        # print res
        write_data_to_xls(dst_addr, tb_head, res)

    @classmethod
    def get_res_from_certain_days(cls, days=1):
        """返回相关日期的用户留存"""