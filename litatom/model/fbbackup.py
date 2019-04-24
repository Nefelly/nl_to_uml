# coding: utf-8
import datetime
import bson
import time
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from ..util import (
    date_from_unix_ts,
    format_standard_time
)

class FaceBookBackup(Document):
    '''
    fb备份数据
    '''
    nickname = StringField(required=True)
    uid = StringField(required=True)
    fbuid = StringField(required=True)
    create_ts = IntField(required=True)

    @classmethod
    def copy_from_old(cls, user):
        obj = cls()
        import json
        extra = user.facebook.extra_data.replace('u\'', '\'').replace('\'', "\"")
        obj.nickname = extra.get('name')
        obj.fbuid = extra.get('id')
        obj.uid = str(user.id)
        obj.create_ts = int(time.time())


    @classmethod
    def get_by_id(cls, track_id):
        if not bson.ObjectId.is_valid(track_id):
            return None
        return cls.objects(id=track_id).first()
