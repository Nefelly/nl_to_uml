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


class UserModel(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    ALERT_TIMES = 2
    user_id = StringField(required=True)
    alert_num = IntField(required=True, default=0)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, user_id):
        obj = cls(user_id=user_id, alert_num=1)
        obj.save()
        return str(obj.id)

    @classmethod
    def add_alert_num(cls, user_id):
        ''' add alert num, return should block now'''
        obj = cls.get_by_user_id(user_id)
        if not obj:
            obj = cls(user_id=user_id, alert_num=1)
        else:
            obj.alert_num += 1
        obj.save()
        if obj.alert_num != 0 and obj.alert_num % cls.ALERT_TIMES == 0:
            return True
        return False

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id).first()
