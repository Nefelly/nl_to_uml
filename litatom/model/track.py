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


class TrackChat(Document):
    '''
    报告的问题
    '''
    content = StringField(required=True)
    uid = StringField(required=True)
    target_uid = StringField()
    create_ts = IntField(required=True)

    @classmethod
    def get_by_id(cls, track_id):
        if not bson.ObjectId.is_valid(track_id):
            return None
        return cls.objects(id=track_id).first()

    def to_json(self):
        if not self:
            return {}
        return {
            'content': self.content,
            'user_id': self.uid,
            'target_user_id': self.target_uid if self.target_uid else '',
            'create_time': format_standard_time(date_from_unix_ts(self.create_ts))
        }


class TrackSpamRecord(Document):
    """
        user's spam word history
        """
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    user_id = StringField(required=True)
    word = StringField()
    pic = StringField()
    dealed = BooleanField(required=True, default=False)
    create_time = IntField(required=True)

    @classmethod
    def create(cls, user_id, word=None, pic=None, dealed_tag=False):
        if (not word and not pic) or (word and pic):
            return False
        if word:
            obj = cls(user_id=user_id, word=word, dealed=dealed_tag)
        else:
            obj = cls(user_id=user_id, pic=pic, dealed=dealed_tag)
        obj.create_time = int(time.time())
        obj.save()
        return True

    @classmethod
    def get_record_by_time(cls, from_ts,to_ts,dealed=True):
        return cls.objects(create_time__gte=from_ts, create_time__lte=to_ts, dealed=dealed)

    @classmethod
    def count_by_time_and_uid(cls, user_id, from_time, to_time, dealed=False):
        """统计user在一段时间范围内被警告次数"""
        return cls.objects(create_time__gte=from_time, create_time__lte=to_time, user_id=user_id, dealed=dealed).count()

    @classmethod
    def count_by_uid(cls, user_id):
        """统计用户历史总共被警告次数"""
        return cls.objects(user_id=user_id).count()
