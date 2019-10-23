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
    User,
    UserAction
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
from ..util import get_times_from_str, next_date, date_to_int_time

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']


class RetainStatService(object):

    @classmethod
    def register_userids(cls, start_d, end_d=None):
        if not end_d:
            end_d = next_date(start_d)
        uids = {}
        for _ in User.objects(create_time__gte=start_d, create_time__lte=end_d):
            uids[str(_.id)] = 1
            # uids.append(str(_.id))
        return uids, len(uids.keys())

    @classmethod
    def start_match(cls, uids, start_d):
        end_d = next_date(start_d)
        m = {}
        tt = 0
        for uid in uids:
            cnt = UserAction.objects(user_id=uid, create_time__gte=date_to_int_time(start_d), create_time__lte=date_to_int_time(end_d),
                                     remark__contains='start').count()
            if cnt > 0:
                m[uid] = 1
                tt += cnt
        return len(m.keys()), m, tt

    @classmethod
    def stat_match_succ(cls, uids, start_d):
        end_d = next_date(start_d)
        m = {}
        for _ in UserAction.objects(action='match', create_time__gte=date_to_int_time(start_d), create_time__lte=date_to_int_time(end_d), remark__contains='uccess'):
            # if 'uccess' not in _.remark:
            #     continue
            uid = _.user_id
            if uid not in uids:
                continue
            if not m.get(uid):
                m[uid] = 1
            else:
                m[uid] += 1
        return len(m.keys()), m

    @classmethod
    def test_all(cls, d='20191021'):
        start_d = get_times_from_str(d)
        m, l = cls.register_userids(start_d)
        print "total", l
        s_match_num, s_m, sm_cnt = RetainStatService.start_match(m, start_d)
        print "started match:%r, match_times:%r" % (s_match_num, sm_cnt)
        succ_num, succ_uids = cls.stat_match_succ(m, start_d)
        print "match success uids:", succ_num
        not_match_succ = {}
        for _ in s_m:
            if _ not in succ_uids:
                not_match_succ[_] = 1
        print "match and fail num", len(not_match_succ.keys())
        nomsucc_ac, nomsuccnum = cls.stat_active(not_match_succ, next_date(start_d))
        print "match and fail active next day", nomsucc_ac, "actions num", nomsuccnum


    @classmethod
    def stat_active(cls, uids, start_d):
        end_d = next_date(start_d)
        m = {}
        for uid in uids:
            if UserAction.objects(user_id=uid, create_time__gte=date_to_int_time(start_d), create_time__lte=date_to_int_time(end_d)).count() > 0:
                m[uid] = 1
        # for _ in UserAction.objects(create_time__gte=date_to_int_time(start_d), create_time__lte=date_to_int_time(end_d)):
        #     uid = _.user_id
        #     if uid not in uids:
        #         continue
        #     if not m.get(uid):
        #         m[uid] = 1
        #     else:
        #         m[uid] += 1
        return len(m.keys()), sum(m.values())
