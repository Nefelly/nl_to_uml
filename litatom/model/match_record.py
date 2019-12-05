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


class MatchRecord(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    low_user_id = StringField(required=True)
    high_user_id = StringField(required=True)
    match_succ_time = IntField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, user_id1, user_id2, ):
        obj = cls()
        if user_id1 < user_id2:
            user_id1
        return str(obj.id)

    @classmethod
    def get_by_id(cls, result_id):
        if not bson.ObjectId.is_valid(result_id):
            return None
        obj = cls.objects(id=result_id).first()
        if obj:
            return json.loads(obj.result)
        return {}

