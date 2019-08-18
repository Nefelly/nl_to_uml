# coding: utf-8
import random
import time
import datetime
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from .. import model
from ..model import *
from ..service import (
    UserService,
    FirebaseService,
    FeedService
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

class MysqlSyncService(object):
    UID_PWDS = {
        'joey': 'hypercycle'
    }

    @classmethod
    def get_tables(cls):
        res = {}
        for _ in dir(model):
            try:
                if globals().get(_, None) and issubclass(globals()[_], Document):
                    res[_] = globals()[_]
            except Exception as e:
                # print _, e
                continue
        return res

    @classmethod
    def table_fields(cls, c):
        res = {}
        for _ in dir(c):
            if 'mongoengine.fields.' in str(type(getattr(c, _))):
                res[_] = type(getattr(c, _))
        return res

    @classmethod
    def all_field_type(cls):
        res = {}
        for c in cls.get_tables().values():
            for f in cls.table_fields(c).values():
                if not res.get(f, None):
                    res[f] = 1
        return res.keys()

    @classmethod
    def check_has_time(cls):
        check_fs = ['create_time', 'create_ts']
        for n,v in cls.get_tables().items():
            fs = cls.table_fields(v)
            r = False
            for _ in check_fs:
                if fs.get(_):
                    r = True
                    break
            if not r:
                print n , fs

    @classmethod
    def c(cls):
        print dir(model)

#print MysqlSyncService.get_tables()
#print MysqlSyncService.table_fields(Avatar)
#print MysqlSyncService.all_field_type()
print MysqlSyncService.check_has_time()
