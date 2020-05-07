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

from ..const import ONE_DAY
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
    duplicated = BooleanField(default=False)
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

    @classmethod
    def set_same_report_to_dealed(cls, uid, target_uid):
        for _ in cls.objects(uid=uid, target_uid=target_uid, dealed=False):
            _.duplicated = True
            _.save()

    @classmethod
    def is_dup_report(cls, uid, target_uid, ts_now):
        if cls.objects(uid=uid,target_uid=target_uid,create_ts__gte=ts_now-3*ONE_DAY, create_ts__lte=ts_now,dealed=False):
            return True
        return False

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
    def count_by_time_and_uid_distinct(cls, user_id, from_time, to_time):
        """返回用户一段时间内被不同人举报次数"""
        return len(cls.objects(target_uid=user_id, create_ts__gte=from_time, create_ts__lte=to_time,dealed=False).distinct("uid"))

    @classmethod
    def count_match_by_time_and_uid(cls, user_id, from_time, to_time):
        """返回用户一段时间内因match被不同人举报次数"""
        return len(cls.objects(target_uid=user_id, create_ts__gte=from_time, create_ts__lte=to_time, reason="match",dealed=False).distinct("uid"))

    @classmethod
    def count_by_time_and_uid(cls, user_id, from_ts, to_ts, dealed=False):
        """返回用户一段时间内被其他人举报次数，不去重"""
        return cls.objects(target_uid=user_id, create_ts__gte=from_ts, create_ts__lte=to_ts, dealed=dealed).count()

    @classmethod
    def get_report_by_time(cls, from_ts, to_ts, dealed=True):
        """返回一段时间内的举报情况"""
        return cls.objects(create_ts__gte=from_ts, create_ts__lte=to_ts, dealed=dealed)

    @classmethod
    def get_report_with_pic_by_time(cls, target_uid, from_ts, to_ts, dealed=False):
        """找出带有feed的举报"""
        return cls.objects(target_uid=target_uid, create_ts__gte=from_ts, create_ts__lte=to_ts, related_feed__ne='', dealed=dealed)

    @classmethod
    def count_report_by_uid(cls, user_id, from_time, to_time):
        """返回用户一段时间内主动举报别人的次数"""
        return cls.objects(uid=user_id, create_ts__gte=from_time, create_ts__lte=to_time).count()
