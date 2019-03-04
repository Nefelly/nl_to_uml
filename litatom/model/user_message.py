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

class UserMessage(Document):
    '''
    用户登录时给用户推送的消息
    '''
    related_feedid = StringField(required=True)
    uid = StringField(required=True)
    related_uid = StringField()
    m_type = StringField(required=True)
    time = DateTimeField(required=True, default=datetime.datetime.now)