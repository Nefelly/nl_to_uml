# coding: utf-8
import random
import time
import datetime
from flask import (
    request
)
from mongoengine.queryset.visitor import Q
from ..model import (
    AdminUser,
    Report,
    Feed,
    User
)
from ..service import (
    UserService,
    FirebaseService,
    FeedService,
    ReportService,
    GlobalizationService
)
from ..const import (
    MAX_TIME
)
from ..redis import RedisClient

from ..key import (
    REDIS_USER_INFO_FINISHED,
    REDIS_ADMIN_USER
)

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

class AdminService(object):
    UID_PWDS = {
        'joey': 'hypercycle'
    }

    @classmethod
    def get_user_name_by_session(cls, session):
        return redis_client.get(REDIS_ADMIN_USER.format(session=session))

    @classmethod
    def gen_session(cls):
        td = datetime.datetime.now() - datetime.datetime(1980, 1, 1)
        ss = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6
        rs = sys_rnd.randint(10 ** 8, 10 ** 8 * 9)
        return 'session.%d%d' % (ss, rs)

    @classmethod
    def login(cls, user_name, pwd):
        """
        登录的动作
        :param user:
        :return:
        """
        admin_user = AdminUser.get_by_user_name(user_name)
        if admin_user and admin_user.pwd == pwd:
            session = admin_user.gen_session()
            return {
                'session': session
            }, True
        return None, False

    @classmethod
    def create(cls, user_name, pwd):
        obj = AdminUser()
        obj.user_name = user_name
        obj.pwd = pwd
        obj.create_time = datetime.datetime.now()
        obj.save()

    @classmethod
    def query_reports(cls, start_ts, num=10, dealed=None):
        if not start_ts:
            start_ts = MAX_TIME
        if not num:
            num = 10
        if dealed in [False, True]:
            objs = Report.objects( (Q(create_ts__lte=start_ts) & Q(dealed=dealed) & Q(region=GlobalizationService.get_region()) & Q(reason__ne='match')) |
                                  (Q(create_ts__lte=start_ts) & Q(dealed=dealed) & Q(region=GlobalizationService.get_region()) &Q(chat_record__ne=None)) ).order_by('-create_ts').limit(num + 1)
        else:
            objs = Report.objects(create_ts__lte=start_ts).order_by('-create_ts').limit(num + 1)
        objs = list(objs)
        has_next = False
        next_start = -1
        if len(objs) == num + 1:
            has_next = True
            next_start = objs[-1].create_ts
            objs = objs[:-1]
        return {
                   'objs': [ReportService.get_report_info(el) for el in objs],
                   'has_next': has_next,
                   'next_start': next_start
               }, True


    @classmethod
    def ban_user_by_report(cls, report_id, ban_time):
        report = Report.get_by_id(report_id)
        if not report:
            return u'wrong report id', False
        user = User.get_by_id(report.target_uid)
        if not user:
            feed = Feed.get_by_id(report.target_uid)
            report.target_uid = feed.user_id
        res = UserService.forbid_user(report.target_uid, ban_time)
        if res:
            report.ban(ban_time)
            UserService.block_actions(report.target_uid, [report.uid])
            return None, True
        return u'forbid error', False

    @classmethod
    def ban_user_by_feed_id(cls, feed_id, ban_time):
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return u'wrong feed id', False
        feed_user_id = feed.user_id
        res = UserService.forbid_user(feed_user_id, ban_time)
        if res:
            for feed in Feed.get_by_user_id(feed_user_id):
                FeedService.delete_feed('', str(feed.id))
            return None, True
        return u'forbid error', False

    @classmethod
    def reject_report(cls, report_id):
        report = Report.get_by_id(report_id)
        if not report:
            return u'wrong report id', False
        report.reject()
        return None, True
