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

class Feedback(Document):
    '''
    报告的问题
    '''
    content = StringField(required=True)
    uid = StringField(required=True)
    pics = ListField(required=False, default=[])
    phone = StringField(required=False)
    deal_res = StringField()
    passed = BooleanField(required=True, default=False)
    create_ts = IntField(required=True)
    deal_ts = IntField()

    @classmethod
    def get_by_id(cls, feedback_id):
        if not bson.ObjectId.is_valid(feedback_id):
            return None
        return cls.objects(id=feedback_id).first()

    def to_json(self):
        if not self:
            return {}
        return {
            'content': self.content,
            'user_id': self.uid,
            'pics': self.pics,
            'phone': self.phone,
            'deal_result': self.deal_res if self.deal_res else '',
            'create_time': format_standard_time(date_from_unix_ts(self.create_ts))
        }