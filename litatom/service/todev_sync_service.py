# coding: utf-8
import json
import time
import traceback
from ..model import (
    UserSetting
)
from ..model import *
from ..util import (
    get_time_int_from_str,
    date_from_unix_ts
)
import logging
from mongoengine.context_managers import switch_db
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
    EmbeddedDocumentField
)
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
    def sync(cls, model, judge_time=None, escape_filed=[]):
        '''
        :param model:
        :param judge_time: create_time__gte=
        :return:
        '''
        dev_objs = []
        with switch_db(model, 'dev_lit') as Model:
            if judge_time:
                real_judge = get_time_int_from_str(judge_time)
                if isinstance(getattr(model, 'create_time'), DateTimeField):
                    real_judge = date_from_unix_ts(real_judge)
                dev_objs = Model.objects(create_time__gte=real_judge)
            else:
                dev_objs = [el for el in Model.objects()]
        fields = cls.table_fields(model)
        for obj in dev_objs:
            query_str = []
            for f in fields:
                if f == 'create_time':
                    continue
                if escape_filed:
                    if f in escape_filed:
                        continue
                value = getattr(obj, f)
                if value is None:
                    continue
                if fields[f] == StringField:
                    tmp = "%s='%s'" % (f, value)
                else:
                    tmp = "%s=%s" % (f, value)
                query_str.append(tmp)
            real_query = '%s.objects(%s).first()' % (model.__name__, ','.join (query_str))
            print real_query
            res = eval(real_query)
            if res:
                res.delete()
            to_save = eval('%s(%s)' % (model.__name__, ','.join (query_str)))
            to_save.save()
        return dev_objs