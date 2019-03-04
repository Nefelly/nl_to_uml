# coding: utf-8
import datetime
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)

class Report(Document):
    '''
    用户登录时给用户推送的消息
    '''
    reason = StringField(required=True)
    uid = StringField(required=True)
    pics = ListField(required=True, default=[])
    deal_res = StringField(required=True)
    passed = BooleanField(required=True, default=False)
    time = DateTimeField(required=True, default=datetime.datetime.now)