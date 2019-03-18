# coding: utf-8
import datetime
import bson
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