# coding: utf-8
import json
import time
import datetime
import traceback
import logging
import mmh3
import random
from flask import (
    request
)
from hendrix.conf import setting
from ..key import (
    REDIS_LOC_USER_ACTIVE
)
from ..util import (
    now_date_key,
    next_date,
    date_from_str
)
from ..const import (
    ONE_DAY,
    VOLATILE_USER_ACTIVE_RETAIN_DAYS,
    ALILOG_GET_LIMIT_NUM
)
from ..model import (
    ExperimentResult
)
from ..service import (
    ExperimentService,
    GlobalizationService,
    UserService,
    AliLogService
)

from ..redis import RedisClient

logger = logging.getLogger(__name__)

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']
volatile_redis = RedisClient()['volatile']

class ExperimentAnalysisService(object):
    BUCKET_NUM = 100

    USER_EXP_TTL = ONE_DAY
    WHITE_LIST_TTL = 30 * ONE_DAY
    STAT_NAMES = [ExperimentResult.RETAIN, ExperimentResult.PAYMENT]

    @classmethod
    def default_exp_values(cls, exp_name):
        '''
        批量获取用户对应实验的value
        :param exp_name:
        :param ids:
        :return:
        先 查询桶对应的value
        再 查询id 对应的桶
        再 返回
        '''
        ids = UserService.get_all_ids()
        bucket_values = ExperimentService.load_bucket_value_m(exp_name)
        values_ids = {}
        for _ in ids:
            bucket = ExperimentService._get_bucket(exp_name, _)
            value = bucket_values.get(bucket)
            if values_ids.get(value, []):
                values_ids[value].add(_)
            else:
                values_ids[value] = set([_])
        values = values_ids.keys()
        other_values = [el for el in values if el != ExperimentService.DEFAULT_VALUE]
        exp_values = []
        other_values_len = len(other_values)
        if other_values_len == 1:
            exp_values = values_ids.get(other_values[0])
        elif other_values_len > 1:
            exp_values = [values_ids.get(el) for el in other_values]
        return values_ids.get(ExperimentService.DEFAULT_VALUE), exp_values, values_ids

    @classmethod
    def get_active_users_by_date(cls, date_time):
        if isinstance(date_time, str):
            date_time = date_from_str(date_time)
        if not isinstance(date_time, datetime.datetime):
            assert False, u'wrong argument of date_time'
        res = []
        date_now = datetime.datetime.now()
        time_diff = (date_now - date_time).total_seconds()
        if time_diff < 0 or time_diff > (VOLATILE_USER_ACTIVE_RETAIN_DAYS - 1) * ONE_DAY:
            print(u'too long to retrieve daily active')
            return res
        date_key = date_time.strftime('%Y-%m-%d')
        for loc in GlobalizationService.LOCS:
            key = REDIS_LOC_USER_ACTIVE.format(date_loc=date_key + loc)
            tmp = volatile_redis.smembers(key)
            res += tmp
        return res

    @classmethod
    def get_tag_by_uid(cls, tag_uids, uid):
        for tag in tag_uids:
            if uid in tag_uids[tag]:
                return tag
        return None

    @classmethod
    def load_uid_payment(cls, tag_uids, from_time, to_time):
        resp = AliLogService.get_log_atom(project='litatom-account', logstore='account_flow',
                                          from_time=AliLogService.datetime_to_alitime(from_time),
                                          to_time=AliLogService.datetime_to_alitime(to_time),
                                          query="name:deposit | SELECT user_id,sum(diamonds) as res GROUP by user_id limit %d" % ALILOG_GET_LIMIT_NUM)
        help_set = {}
        res = {}
        for tag in tag_uids:
            help_set[tag]['pay_num'] = set()
            res[tag]['pay_sum'] = 0.0
        for log in resp.logs:
            content = log.get_contents()
            user_id = content['user_id']
            res = content['res']

            tag = cls.get_tag_by_uid(tag_uids, user_id)
            if tag:
                res[tag]['pay_sum'] += int(res)
                help_set[tag].add(user_id)

        for tag in res:
            res[tag]['pay_num'] = len(help_set[tag])
        return res

    @classmethod
    def get_exp_active_uids(cls, exp_name, date_str):
        '''
        :param exp_name:
        :param date_str:
        :return:{'default': set(1, 2, 3)}
        '''
        default, exp, tag_ids = cls.default_exp_values(exp_name)
        active_uids = cls.get_active_users_by_date(date_str)
        res = {}
        for tag in tag_ids:
            res[tag] = tag_ids[tag] & active_uids
        return res

    @classmethod
    def tag_retains(cls, tag_uids, stat_date):
        stat_actives = cls.get_active_users_by_date(stat_date)
        res = {}
        for tag in tag_uids:
            active_num = len(tag_uids[tag] & stat_actives)
            res[tag] = {
                'active_num': active_num,
                'retain_rate': active_num * 1.0 / len(tag_uids[tag])
            }
        return res

    @classmethod
    def record_result(cls, tag_uids, cal_ress, exp_name, date_str, name):
        for tag in tag_uids:
            res = cal_ress[tag]
            res['total_num'] = len(tag_uids[tag])
            result_date = date_from_str(date_str)
            ExperimentResult.create(exp_name, tag, result_date, name, res)

    @classmethod
    def cal_day_result(cls, date_str, exp_name):
        date_time = date_from_str(date_str)
        anchor_yestoday = next_date(date_time, -1)
        anchor_tomorrow = next_date(date_time)

        today_exp_actives = cls.get_exp_active_uids(exp_name, date_str)
        payment_res = cls.load_uid_payment(today_exp_actives, date_time, anchor_tomorrow)
        cls.record_result(today_exp_actives, payment_res, exp_name, date_time, ExperimentResult.PAYMENT)

        yestoday_exp_actives = cls.get_exp_active_uids(exp_name, anchor_yestoday)
        retain_res = cls.tag_retains(yestoday_exp_actives, date_time)
        cls.record_result(yestoday_exp_actives, retain_res, exp_name, date_time, ExperimentResult.RETAIN)