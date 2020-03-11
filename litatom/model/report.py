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


class Report(Document):
    '''
    报告的问题
    '''
    reason = StringField(required=True)
    # match_type = StringField(required=True)
    uid = StringField(required=True)
    target_uid = StringField()
    pics = ListField(required=False, default=[])
    chat_record = StringField()
    deal_res = StringField()
    dealed = BooleanField(required=True, default=False)
    deal_user = StringField()
    related_feed = StringField()
    region = StringField()
    # passed = StringField()
    create_ts = IntField(required=True)
    deal_ts = IntField()

    @classmethod
    def get_by_id(cls, report_id):
        if not bson.ObjectId.is_valid(report_id):
            return None
        return cls.objects(id=report_id).first()

    def to_json(self, *args, **kwargs):
        if not self:
            return {}
        tmp = super(Report, self).to_json(*args, **kwargs)
        import json
        tmp = json.loads(tmp)
        tmp['create_time'] = format_standard_time(date_from_unix_ts(self.create_ts))
        return tmp
        # return {
        #     'reason': self.reason,
        #     'report_id': str(self.id),
        #     'user_id': self.uid,
        #     'pics': self.pics,
        #     'chat_record': self.chat_record,
        #     'related_feed': self.related_feed,
        #     'deal_result': self.deal_res if self.deal_res else '',
        #     'target_user_id': self.target_uid if self.target_uid else '',
        #     'create_time': format_standard_time(date_from_unix_ts(self.create_ts))
        # }

    def ban(self, ban_time):
        self.dealed = True
        self.deal_ts = int(time.time())
        self.deal_res = str(ban_time)
        self.save()
        return True

    def reject(self):
        self.dealed = True
        self.deal_ts = int(time.time())
        self.deal_res = 'reject'
        self.save()
        return True

    @classmethod
    def count_by_time_and_uid(cls, user_id, from_time, to_time):
        """返回用户一段时间内被不同人举报次数"""
        return len(cls.objects(target_uid=user_id, create_ts__gte=from_time, create_ts__lte=to_time,dealed=False).distinct("uid"))

    @classmethod
    def count_match_by_time_and_uid(cls, user_id, from_time, to_time):
        """返回用户一段时间内因match被不同人举报次数"""
        return len(cls.objects(target_uid=user_id, create_ts__gte=from_time, create_ts__lte=to_time, reason="match",dealed=False).distinct("uid"))

    @classmethod
    def count_report_by_uid(cls, user_id, from_time, to_time):
        """返回用户一段时间内主动举报别人的次数"""
        return cls.objects(uid=user_id, create_ts__gte=from_time, create_ts__lte=to_time).count()
