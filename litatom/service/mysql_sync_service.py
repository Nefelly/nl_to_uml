# coding: utf-8
import random
import time
import datetime
import MySQLdb
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
    EmbeddedDocumentField
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

'''
<class 'mongoengine.fields.StringField'>,
<class 'mongoengine.fields.IntField'>,
<class 'mongoengine.fields.ListField'>,
<class 'mongoengine.fields.EmbeddedDocumentField'>,
<class 'mongoengine.fields.DateTimeField'>,
<class 'mongoengine.fields.BooleanField'>
'''

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

def get_dbcnn():
    db = MySQLdb.connect("120.24.201.118", "lit", "asd1559", "lit", charset='utf8')
    return db

class MysqlSyncService(object):
    BIGGEST_LIST = 1024
    BIGGEST_EMBEDDED = 1024
    LIMIT_ROWS = 2000
    QUERY_AMOUNT = 100
    UPSERT_MAX = 10
    MONGO_MYSQL = {
        StringField: 'VARCHAR (255)',
        IntField: 'int(13)',
        ListField: 'VARCHAR(%d)' % BIGGEST_LIST,
        EmbeddedDocumentField:  'VARCHAR(%d)' % BIGGEST_EMBEDDED,
        DateTimeField: 'datetime',
        BooleanField: 'tinyint(1)'
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
    def _get_time_field(cls, c):
        check_fs = ['create_time', 'create_ts']
        fs = cls.table_fields(c)
        for _ in check_fs:
            if fs.get(_):
                return _ , fs.get(_)
        assert False

    @classmethod
    def check_has_time(cls):
        check_fs = ['create_time', 'create_ts']
        for n,v in cls.get_tables().items():
            fs = cls.table_fields(v)
            r = False
            print n, fs
            for _ in check_fs:
                if fs.get(_):
                    r = True
                    break
            if not r:
                print n , fs

    @classmethod
    def gen_ddl(cls, c):
        def gen_filed(name, t):
            return "`%s` %s," % (name, cls.MONGO_MYSQL[t])

        mode = '''
          CREATE TABLE IF NOT EXISTS `%s` (
          `id` VARCHAR(64) NOT NULL,
          %s
          PRIMARY KEY (`id`),
          UNIQUE KEY `indmid` (`mid`),
          INDEX `ctime` (`%s`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'''

        tb_name = c.__name__

        fields = '\n'.join([gen_filed(name, t) for name, t in cls.table_fields(c).items()])
        ctime_name = cls._get_time_field(c)
        return mode % (tb_name, fields, ctime_name[0])

    @classmethod
    def execute(cls, sql):
        db = get_dbcnn()
        db.cursor().execute(sql)
        db.commit()

    @classmethod
    def fetch_one(cls, sql):
        db = get_dbcnn()
        cursor = db.cursor()
        cursor.execute(sql)
        return cursor.fetchone()

    @classmethod
    def fetch_all(cls, sql):
        db = get_dbcnn()
        cursor = db.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    @classmethod
    def create_tables(cls):
        db = get_dbcnn()
        for tb in cls.get_tables().values():
            ddl = cls.gen_ddl(tb)
            # print ddl
            db.cursor().execute(ddl)
            db.commit()
            break

    @classmethod
    def mongo_val_2_sql(cls, value, t):
        if value == None:
            return {
                StringField: '',
                IntField: 0,
                ListField: '' ,
                EmbeddedDocumentField:  '',
                DateTimeField: '0:0:0 00:00:00',
                BooleanField: False
            }.get(t)


    @classmethod
    def update_tb(cls, c):
        tb_name = c.__name__
        create_name, t = cls._get_time_field(c)
        max_sql = 'SELECT MAX(%s) FROM %s;' % (create_name, tb_name)
        print max_sql

        cond = cls.fetch_one(max_sql)
        if not cond[0]:
            cond = 0 if t == IntField else '0-0-0 00:00:00'

        mongo_get = '%s.objects(%s__gte=%r).order_by(\'%s\').limit(%d)' % (tb_name, create_name, cond, create_name, cls.QUERY_AMOUNT)
        print mongo_get
        mongo_res = eval(mongo_get)
        print mongo_res
        colums = []
        valuse = []
        upsert_sql = 'INSERT IGNORE INTO %s (%s) VALUES (%s);' % (tb_name, )

    @classmethod
    def c(cls):
        print dir(model)


print MysqlSyncService.update_tb(UserAction)