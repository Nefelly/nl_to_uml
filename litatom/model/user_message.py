# coding: utf-8
import time
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


    related_feedid = StringField()
    uid = StringField(required=True)
    related_uid = StringField()
    m_type = StringField(required=True)
    content = StringField()
    create_time = IntField(required=True)

    @classmethod
    def get_by_id(cls, message_id):
        return cls.objects(id=message_id).first()

    @classmethod
    def add_message(cls, user_id, related_user_id, m_type, related_feed_id=None, content=None):
        if user_id == related_user_id:
            return None
        obj = cls()
        obj.uid = user_id
        obj.related_uid = related_user_id
        obj.m_type = m_type
        if related_feed_id:
            obj.related_feedid = related_feed_id
        if content:
            obj.content = content
        obj.create_time = int(time.time())
        obj.save()
        return str(obj.id)