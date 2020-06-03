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
    REDIS_EXP,

)
from ..util import (

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
    GlobalizationService
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
    def batch_get_value_ids(cls, exp_name, ids, value=None):
        '''
        批量获取用户对应实验的value
        :param exp_name:
        :param ids:
        :return:
        先 查询桶对应的value
        再 查询id 对应的桶
        再 返回
        '''
        bucket_values = cls.load_bucket_value_m(exp_name)
        values_ids = {}
        for _ in ids:
            bucket = cls._get_bucket(exp_name, _)
            value = bucket_values.get(bucket)
            if values_ids.get(value, []):
                values_ids[value].append(_)
            else:
                values_ids[value] = [_]
        if value:
            return values_ids.get(value, [])
        return values_ids

    @classmethod
    def get_active_users_by_date(cls, date_time):
        date_now = datetime.datetime.now()
        date_key = now_date_key(datetime.timedelta(days=-VOLATILE_USER_ACTIVE_RETAIN_DAYS))
        for loc in GlobalizationService.LOCS:
            to_rem_key = REDIS_LOC_USER_ACTIVE(date_loc=date_key + loc)
