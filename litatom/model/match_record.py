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


    user_id1 = StringField(required=True)
    user_id2 = StringField(required=True)
    match_type = StringField(required=True)
    quit_user = StringField()
    match_succ_time = IntField()
    inter_time = IntField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, user_id1, user_id2, match_type, quit_user, match_succ_time, inter_time):
        obj = cls()
        obj.user_id1 = user_id1
        obj.user_id2 = user_id2
        obj.match_type = match_type
        obj.quit_user = quit_user
        obj.match_succ_time = match_succ_time
        obj.inter_time = inter_time
        obj.save()
        return obj
