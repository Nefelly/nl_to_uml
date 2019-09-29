# coding: utf-8
import datetime
import json
import bson
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)

class ReferralCode(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    code = StringField(required=True)
    user_id = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, user_id, code):
        if cls.get_by_user_id(user_id):
            return
        obj = cls()
        obj.code = code
        obj.user_id = user_id
        obj.save()
        return str(obj.id)

    @classmethod
    def get_by_user_id(cls, user_id):
        if not bson.ObjectId.is_valid(user_id):
            return None
        obj = cls.objects(user_id=user_id).first()
        if obj:
            return obj

