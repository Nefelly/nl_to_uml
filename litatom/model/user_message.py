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

class UserConversation(Document):
    '''
    用户登录时给用户推送的消息
    '''

    user_id = StringField(required=True)
    other_user_id = StringField()
    conversation_id = StringField(required=True)
    from_type = StringField()
    create_time = IntField(required=True)

    @classmethod
    def get_by_user_id(cls, user_id):
        return [el.to_json() for el in cls.objects(user_id=user_id).order_by('-create_time').limit(100)]

    def to_json(self, *args, **kwargs):
        return {
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'create_time': self.create_time
        }

    @classmethod
    def add_conversation(cls, user_id, other_user_id, conversation_id, from_type=None):
        obj = cls(user_id=user_id, other_user_id=other_user_id, conversation_id=conversation_id)
        if from_type:
            obj.from_type = from_type
        obj.save()
        return True

    @classmethod
    def get_by_user_id_conversation_id(cls, user_id, conversation_id):
        return cls.objects(user_id=user_id, conversation_id=conversation_id).first()

    @classmethod
    def del_conversation(cls, user_id, conversation_id):
        cls.objects(user_id=user_id, conversation_id=conversation_id).delete()
        return True
