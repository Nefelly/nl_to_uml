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
from ..util import get_times_from_str, next_date

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']


class RetainStatService(object):

    @classmethod
    def register_userids(cls, start_d, end_d):
        uids = []
        for _ in User.objects(create_time__gte=start_d, create_time__lte=end_d):
            uids.append(str(_.id))
        return uids, len(uids)

    @classmethod
    def stat_match_succ(cls, uids, start_d):
        end_d = next_date(start_d)
        m = {}
        for _ in UserAction.objects(action='match', create_date__gte=start_d, create_date__lte=end_d, remark__contains='uccess'):
            uid = _.user_id
            if not m.get(uid):
                m[uid] = 1
            else:
                m[uid] += 1
        return len(m.keys()), sum(m.values())

    @classmethod
    def stat_active(cls, uids, start_d):
        end_d = next_date(start_d)
        m = {}
        for _ in UserAction.objects(create_date__gte=start_d, create_date__lte=end_d):
            uid = _.user_id
            if not m.get(uid):
                m[uid] = 1
            else:
                m[uid] += 1
        return len(m.keys()), sum(m.values())
