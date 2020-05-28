# coding: utf-8
import datetime
import random
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from .. util import (
    get_times_from_str,
    next_date
)
from ..const import (
    ONE_DAY
)
from ..redis import RedisClient

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']


class OperateRecord(Document):
    '''
    用于记录操作的历史记录 用来进行恢复
    '''
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    data = StringField(required=True)
    name = StringField(required=True)
    is_table = BooleanField(default=False)
    user_id = StringField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_date_name(cls, name, date_str):
        int_time, real_date = get_times_from_str(date_str)
        next = next_date(real_date)
        return cls.objects(name=name, create_time__gte=real_date, create_time__lte=next)

    @classmethod
    def add(cls, name, data, is_table=False, user_id=None):
        obj = cls(name=name, data=data, is_table=is_table, user_id=user_id)
        obj.save()
