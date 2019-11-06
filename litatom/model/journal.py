# coding: utf-8
import datetime
import bson
import time
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from ..util import (
    date_from_unix_ts,
    format_standard_time
)

class StatItems(Document):
    '''
    统计表设计
    '''
    name = StringField(required=True)
    table_name = StringField(required=True)
    judge_field = StringField()
    expression = StringField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, name, table_name, judge_field='', expression=''):
        obj = cls(name=name, table_name=table_name)
        if judge_field:
            obj.judge_field =judge_field
        if expression:
            obj.expression = expression
        obj.save()

    def to_json(self, *args, **kwargs):
        tmp = super(StatItems, self).to_json(*args, **kwargs)
        import json
        tmp = json.loads(tmp)
        tmp['id'] = str(self.id)
        return tmp
