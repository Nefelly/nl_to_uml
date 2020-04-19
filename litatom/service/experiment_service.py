# coding: utf-8
import json
import time
import traceback
import logging
from flask import (
    request
)
from hendrix_conf import setting
from ..key import (
    REDIS_EXP
)
from ..const import (
    ONE_DAY
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class ExperimentService(object):
    '''
    '''

    @classmethod
    def _get_key(cls, key, exp_name):
        key_exp = '%s_%s' % (key, exp_name)
        return REDIS_EXP.format(key_exp=key_exp)

    @classmethod
    def set_exp(cls, key=None, expire=ONE_DAY):
        if not key:
            key = request.user_id
        if key is None:
            return True
        exp_name = request.experiment_name
        if not exp_name:
            return
        exp_value = request.experiment_value
        if exp_value == 'default':
            '''测试环境可以重新设置值'''
            if setting.IS_DEV:
                redis_client.delete(cls._get_key(key, exp_name))
            return
        if exp_value is None:
            return
        redis_client.set(cls._get_key(key, exp_name), exp_value, ex=expire)
        return True

    @classmethod
    def get_exp_value(cls, exp_name, key=None):
        if not key:
            key = request.user_id
        return redis_client.get(cls._get_key(key, exp_name))
