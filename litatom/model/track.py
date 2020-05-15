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
from ..const import (
    SPAM_RECORD_UNKNOWN_SOURCE
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
    forbid_weight = IntField(required=True, default=SPAM_RECORD_UNKNOWN_SOURCE)
    source = StringField(required=True)

    @classmethod
    def create(cls, user_id, word=None, pic=None, dealed_tag=False, forbid_weight=0, source=SPAM_RECORD_UNKNOWN_SOURCE):
        if (not word and not pic) or (word and pic):
            return False
        if word:
            obj = cls(user_id=user_id, word=word, dealed=dealed_tag, source=source)
        else:
            obj = cls(user_id=user_id, pic=pic, dealed=dealed_tag, source=source)
        obj.create_time = int(time.time())
        obj.forbid_weight = forbid_weight
        obj.save()
        return True

    @classmethod
    def get_record_by_time(cls, from_ts, to_ts, dealed=True):
        return cls.objects(create_time__gte=from_ts, create_time__lte=to_ts, dealed=dealed)

    @classmethod
    def get_record_by_id(cls, record_id):
        return cls.objects(id=record_id).first()

    @classmethod
    def get_records_by_uid_and_time(cls, user_id, from_ts, to_ts, dealed=True):
        return cls.objects(user_id=user_id, create_time__gte=from_ts, create_time__lte=to_ts, dealed=dealed)

    @classmethod
    def count_by_time_and_uid(cls, user_id, from_time, to_time, dealed=False):
        """统计user在一段时间范围内被警告次数"""
        return cls.objects(create_time__gte=from_time, create_time__lte=to_time, user_id=user_id, dealed=dealed).count()

    @classmethod
    def get_alert_score_by_time_and_uid(cls, user_id, from_time, to_time):
        """计算user一段时间范围内的因spam record产生的forbid score"""
        objs = cls.objects(create_time__gte=from_time, create_time__lte=to_time, user_id=user_id, dealed=False)
        res = 0.0
        for obj in objs:
            res += obj.forbid_weight
        return res

    @classmethod
    def count_by_uid(cls, user_id):
        """统计用户历史总共被警告次数"""
        return cls.objects(user_id=user_id).count()

    @classmethod
    def get_review_pic(cls, limit_num=10000):
        return cls.objects(dealed=False, forbid_weight=0, pic__ne=None).order_by('-create_time').limit(limit_num)
