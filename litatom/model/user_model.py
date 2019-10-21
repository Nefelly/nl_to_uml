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


class LoginRecord(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    result = StringField(required=True)
    user_id = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, result, user_id):
        obj = cls()
        obj.result = json.dumps(result)
        obj.user_id = user_id
        obj.save()
        return str(obj.id)

    @classmethod
    def get_by_id(cls, result_id):
        if not bson.ObjectId.is_valid(result_id):
            return None
        obj = cls.objects(id=result_id).first()
        if obj:
            return json.loads(obj.result)
        return {}

