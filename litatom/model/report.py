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

class Report(Document):
    '''
    报告的问题
    '''
    reason = StringField(required=True)
    uid = StringField(required=True)
    target_uid = StringField()
    pics = ListField(required=False, default=[])
    deal_res = StringField()
    passed = BooleanField(required=True, default=False)
    create_ts = IntField(required=True)
    deal_ts = IntField()

    @classmethod
    def get_by_id(cls, report_id):
        if not bson.ObjectId.is_valid(report_id):
            return None
        return cls.objects(id=report_id).first()

    def to_json(self):
        if not self:
            return {}
        return {
            'reason': self.reason,
            'report_id': str(self.id),
            'user_id': self.uid,
            'pics': self.pics,
            'deal_result': self.deal_res if self.deal_res else '',
            'target_user_id': self.target_uid if self.target_uid else '',
            'create_time': format_standard_time(date_from_unix_ts(self.create_ts))
        }
