# coding: utf-8
import json
import time
import traceback
from ..model import (
    UserSetting
)
from ..util import (
    get_time_int_from_str,
    date_from_unix_ts
)
import logging
from mongoengine.context_managers import switch_db
import mongoengine
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class ToDevSyncService(object):
    '''
    '''
    @classmethod
    def test(cls):
        with switch_db(UserSetting, 'dev_lit') as UserSetting:
            print UserSetting.objects().count()

    @classmethod
    def table_fields(cls, c):
        res = {}
        for _ in dir(c):
            if 'mongoengine.fields.' in str(type(getattr(c, _))):
                res[_] = type(getattr(c, _))
        return res

    @classmethod
    def sync(cls, model, judge_time=None):
        '''
        :param model:
        :param judge_time: create_time__gte=
        :return:
        '''
        dev_objs = []

        with switch_db(model, 'dev_lit') as Model:
            if judge_time:
                real_judge = get_time_int_from_str(judge_time)
                if isinstance(getattr(model, 'create_time'), mongoengine.fields.DateTimeField):
                    real_judge = date_from_unix_ts(real_judge)
                dev_objs = Model.objects(create_time__gte=real_judge)
            else:
                dev_objs = [el for el in Model.objects()]
        return dev_objs