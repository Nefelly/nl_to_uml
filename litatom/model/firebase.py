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

class FirebaseInfo(Document):
    '''
    firebase 信息存储
    '''
    user_id = StringField(required=True)
    user_token = StringField(required=True)
    create_time = IntField(required=True)

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id).first()