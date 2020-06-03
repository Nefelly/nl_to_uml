# coding: utf-8
import datetime
import random
import json
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from ..const import (
    ONE_DAY
)
from ..redis import RedisClient

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']


class ExperimentResult(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    RETAIN = 'retain'
    PAYMENT = 'payment'

    exp_name = StringField(required=True)
    tag = StringField()
    result_date = DateTimeField()
    stat_name = StringField()
    res = StringField()
    active_user = IntField(default=0)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, exp_name, tag, result_date, stat_name, res):
        obj = cls.get_by_args(exp_name, tag, result_date, stat_name)
        res = json.dumps(res)
        if obj:
            obj.res = res
            # obj.save()
            # return obj
        else:
            obj = cls(exp_name=exp_name, tag=tag, result_date=result_date, stat_name=stat_name, res=res)
        obj.save()
        return obj

    @classmethod
    def get_by_args(cls, exp_name, tag, result_date, stat_name):
        return cls.objects(exp_name=exp_name, tag=tag, result_date=result_date, stat_name=stat_name).first()

    @classmethod
    def get_by_exp_name_date_name(cls, exp_name, result_date, stat_name):
        return cls.objects(exp_name=exp_name, result_date=result_date, stat_name=stat_name)

    @classmethod
    def desc_dates(cls, exp_name):
        return cls.objects(exp_name=exp_name).order_by('-result_date').distinct('result_date')

    def get_res(self):
        return json.loads(self.res)