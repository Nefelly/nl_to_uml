# coding: utf-8
import time
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
    meta = {
        'strict': False,
        'db_alias': 'relations',
        'shard_key': {'uid': 'hashed'}
    }

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
    meta = {
        'strict': False,
        'db_alias': 'relations',
        'shard_key': {'user_id': 'hashed'}
    }
    MAX_QUERY_NUM = 100
    user_id = StringField(required=True)
    other_user_id = StringField()
    conversation_id = StringField(required=True)
    pinned = BooleanField(default=False)
    from_type = StringField()
    create_time = DateTimeField(required=True, default=lambda: datetime.datetime.now)

    @classmethod
    def get_by_user_id(cls, user_id):
        objs = cls.objects(user_id=user_id).order_by('-create_time').limit(cls.MAX_QUERY_NUM)
        return [el.to_json() for el in objs]

    @classmethod
    def get_pinned_conversation(cls, user_id):
        return cls.objects(user_id=user_id, pinned=True).first()

    def to_json(self, *args, **kwargs):
        return {
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'create_time': self.create_time
        }

    @classmethod
    def pin_conversation_id(cls, user_id, other_user_id, conversation_id):
        obj = cls.get_by_user_id_conversation_id(user_id, conversation_id)
        if not obj:
            obj = cls(user_id=user_id, other_user_id=other_user_id, conversation_id=conversation_id)
        obj.pinned = True
        obj.save()

    @classmethod
    def unpin_conversation_id(cls, user_id, conversation_id):
        obj = cls.get_by_user_id_conversation_id(user_id, conversation_id)
        if obj:
            if obj.pinned:
                obj.pinned = False
                obj.save()


    @classmethod
    def add_conversation(cls, user_id, other_user_id, conversation_id, from_type=None):
        if cls.get_by_user_id_conversation_id(user_id, conversation_id):
            return True
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
