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
    VOLATILE_USER_ACTIVE_RETAIN_DAYS
)
from ..model import (
    ExpBucket
)
from ..service import (
    ExperimentService,
    GlobalizationService,
    UserService
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
                values_ids[value].append(_)
            else:
                values_ids[value] = [_]
        values = values_ids.keys()
        other_values = [el for el in values if el != ExperimentService.DEFAULT_VALUE]
        exp_values = []
        other_values_len = len(other_values)
        if other_values_len == 1:
            exp_values = values_ids.get(exp_values[0])
        elif other_values_len > 1:
            exp_values = [values_ids.get(el) for el in other_values]
        return values_ids.get(ExperimentService.DEFAULT_VALUE), exp_values

    @classmethod
    def get_active_users_by_date(cls, date_time):
        if isinstance(date_time, str):
            date_time = date_from_str(date_time)
        if not isinstance(date_time, datetime):
            assert False, u'wrong argument of date_time'
        res = []
        date_now = datetime.datetime.now()
        time_diff = (date_now - date_time).total_seconds()
        if time_diff < 0 or time_diff > (VOLATILE_USER_ACTIVE_RETAIN_DAYS - 1) * ONE_DAY:
            print(u'too long to retrieve daily active')
            return res
        date_key = date_time.strftime('%Y-%m-%d')
        for loc in GlobalizationService.LOCS:
            key = REDIS_LOC_USER_ACTIVE(date_loc=date_key + loc)
            tmp = volatile_redis.smembers(key)
            res += tmp
        return res
