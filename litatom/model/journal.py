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
    AD_TYPE = 'ad'
    BUSINESS_TYPE = 'business'
    name = StringField(required=True)
    table_name = StringField(required=True)
    judge_field = StringField()
    expression = StringField()
    stat_type = StringField(required=True, default=BUSINESS_TYPE)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, name, table_name, stat_type, judge_field='', expression=''):
        obj = cls(name=name, table_name=table_name, stat_type=stat_type)
        if judge_field:
            obj.judge_field =judge_field
        if expression:
            obj.expression = expression
        obj.save()

    @classmethod
    def get_items_by_type(cls, item_type):
        return cls.objects(stat_type=item_type)

    @classmethod
    def get_by_id(cls, item_id):
        return cls.objects(id=item_id).first()

    def to_json(self, *args, **kwargs):
        return {
            "id": str(self.id),
            "name": self.name,
            "table_name": self.table_name,
            "create_time": str(self.create_time),
            "judge_field": self.judge_field,
            "expression": self.expression
        }
        # tmp = super(StatItems, self).to_json(*args, **kwargs)
        # import json
        # tmp = json.loads(tmp)
        # tmp['id'] = str(self.id)
        # return tmp
