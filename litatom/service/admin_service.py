# coding: utf-8
import random
import string
import time
import os
import datetime
from flask import (
    request
)
from mongoengine.queryset.visitor import Q
from ..model import *
from ..model import (
    AdminUser,
    Report,
    Feed,
    User
)
from ..util import (
    get_args_from_db
)
from ..service import (
    UserService,
    FirebaseService,
    FeedService,
    ReportService,
    GlobalizationService
)
from ..const import (
    MAX_TIME,
    ONE_DAY
)
from ..redis import RedisClient

from ..key import (
    REDIS_USER_INFO_FINISHED,
    REDIS_ADMIN_USER,
    REDIS_REGION_FEED_TOP
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
    def is_top(cls, feed_id):
        top_feed_id = redis_client.get(REDIS_REGION_FEED_TOP.format(region=GlobalizationService.get_region()))
        return top_feed_id == feed_id

    @classmethod
    def add_to_top(cls, feed_id):
        redis_client.set(REDIS_REGION_FEED_TOP.format(region=GlobalizationService.get_region()), feed_id, 30 * ONE_DAY)
        return None, True

    @classmethod
    def remove_from_top(cls, feed_id):
        redis_client.delete(REDIS_REGION_FEED_TOP.format(region=GlobalizationService.get_region()))
        return None, True

    @classmethod
    def get_official_feed(cls, user_id, start_ts, num):
        region = GlobalizationService.get_region()
        # nickname = 'Lit official'
        nickname = 'Lit official(%s)' % region
        # if region == GlobalizationService.REGION_VN:
        #     nickname = 'Lit official(vi)'
        user = User.get_by_nickname(nickname)
        if not user:
            return u'user not exists', False
        uid = str(user.id)
        feeds = Feed.objects(user_id=uid, create_time__lte=start_ts).order_by('-create_time').limit(num + 1)
        feeds = list(feeds)
        next_start = -1
        has_next = False
        if len(feeds) == num + 1:
            has_next = True
            next_start = feeds[-1].create_time
            feeds = feeds[:-1]
        res = []
        for feed in feeds:
            info = FeedService._feed_info(feed, user_id)
            info['in_top'] = cls.is_top(str(feed.id))
            res.append(info)
        return {
                   'feeds': res,
                   'has_next': has_next,
                   'next_start': next_start
               }, True

    @classmethod
    def query_reports(cls, start_ts, num=10, dealed=None):
        if not start_ts:
            start_ts = MAX_TIME
        if not num:
            num = 10
        if dealed in [False, True]:
            objs = Report.objects(create_ts__lte=start_ts, dealed=dealed, region=GlobalizationService.get_region()).filter((Q(reason__ne='match') & Q(reason__ne='video_match') & Q(reason__ne='voice_match')) | Q(chat_record__ne=None)).order_by('-create_ts').limit(num + 1)
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
            if feed:
                report.target_uid = feed.user_id
        res = UserService.forbid_user(report.target_uid, ban_time)
        if res:
            report.ban(ban_time)
            UserService.block_actions(report.target_uid, [report.uid])
            return None, True
        return u'forbid error', False

    @classmethod
    def ban_by_uid(cls, user_id):
        num = Report.objects(uid=user_id).count()
        if not num >= 2:
            return u'user not reported too much', False
        res = UserService.forbid_user(user_id, 20 * ONE_DAY)
        return None, True

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

    @classmethod
    def mongo_gen_csv(cls, table_name, query, fields):
        dir_name = '/tmp/'
        save_add = os.path.join(dir_name, '%s_%d.csv' % (table_name, int(time.time())))
        host, port, user, pwd, db = get_args_from_db('DB_LIT')
        sql = '''mongoexport -h %s --port %r -u %s -p %s --authenticationDatabase lit -d lit -c user_action -f %s --type=csv -q '%s' --out %s''' % (
        host, port, user, pwd, fields, query, save_add)
        os.popen(sql)
        return save_add, True

    @classmethod
    def batch_insert(cls, table_name, fields, main_key, insert_data):
        def check_valid_string(word):
            chars = string.ascii_letters + '_' + string.digits
            for chr in word:
                if chr not in chars:
                    return False
            return True
        NOT_ALLOWED = ["User", "Feed"]
        table_name = table_name.strip()
        fields = fields.strip().split("|")
        main_key = main_key if main_key else ''
        main_key = main_key.strip()
        for el in fields + [table_name, main_key]:
            if not check_valid_string(el):
                return u'word: %s is invalid' % el, False
        insert_data = insert_data.strip()
        if table_name in NOT_ALLOWED:
            return u'Insert into table:%s is not allowed' % table_name, False
        lines = [el.split("\t") for el in insert_data.split("\n") if el]
        for line in lines:
            if len(line) != len(fields):
                return u'len(line) != len(fields), line:%r' % line, False
            conn = ','.join(['%s=\'%s\'' % (fields[i], line[i]) for i in range(len(line))])
            get = eval('%s.objects(%s).first()' % (table_name, conn))
            if not get:
                eval('%s(%s).save()' % (table_name, conn))
        return None, True
