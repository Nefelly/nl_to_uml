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
from ..CMysql import CMysql
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
    LIST_MAX = 1023
    EMBEDDED_MAX = 1023
    STRING_MAX = 255

    LIMIT_ROWS = 200
    QUERY_AMOUNT = 100
    UPSERT_MAX = 1
    MONGO_MYSQL = {
        StringField: 'VARCHAR (%d)' % STRING_MAX,
        IntField: 'int(13)',
        ListField: 'VARCHAR(%d)' % LIST_MAX,
        EmbeddedDocumentField:  'VARCHAR(%d)' % EMBEDDED_MAX,
        DateTimeField: 'timestamp NOT NULL DEFAULT \'0000-00-00 00:00:00\'',
        BooleanField: 'tinyint(1)'
    }
    db = CMysql("120.24.201.118", 3306, "lit", "asd1559", "lit", "utf8")
    # MySQLdb.connect("120.24.201.118", "lit", "asd1559", "lit", charset='utf8')


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
          INDEX `ctime` (`%s`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'''

        tb_name = c.__name__

        fields = '\n'.join([gen_filed(name, t) for name, t in cls.table_fields(c).items()])
        ctime_name = cls._get_time_field(c)
        return mode % (tb_name, fields, ctime_name[0])

    @classmethod
    def execute(cls, sql):
        # db = get_dbcnn()
        cls.db.query(sql)
        # db = cls.db
        # db.cursor().execute(sql)
        # db.commit()

    @classmethod
    def fetch_one(cls, sql):
        # db = get_dbcnn()
        return cls.db.queryRow(sql)[0]
        # db = cls.db
        # cursor = db.cursor()
        # cursor.execute(sql)
        # res = cursor.fetchone()
        # db.commit()
        # # print res
        # return res[0]

    @classmethod
    def fetch_all(cls, sql):
        # db = get_dbcnn()
        return cls.db.queryAll(sql)
        # db = cls.db
        # cursor = db.cursor()
        # cursor.execute(sql)
        # return cursor.fetchall()

    @classmethod
    def create_table(cls, tb):
        # db = get_dbcnn()
        db = cls.db
        ddl = cls.gen_ddl(tb)
        # print ddl
        cls.execute(ddl)
        # db.commit()

    @classmethod
    def mongo_val_2_sql(cls, value, t):
        if isinstance(value, str):
            print 'get in escape str', value
            value = cls.db.escape_string(value)
        def trunc(v, length):
            if len(v) > length:
                return "'%s'" % v.decode('utf-8')[:length].encode('utf-8')
            return v
        if not value:
            return {
                StringField: "''",
                IntField: "0",
                ListField: "''" ,
                EmbeddedDocumentField:  "''",
                DateTimeField: "'1:1:1 00:00:00'",
                BooleanField: "0"
            }.get(t)
        if t == StringField:
            tmp_res =  "'%s'" % value
            return trunc(tmp_res, cls.STRING_MAX)
        elif t == DateTimeField:
            return "'%s'" % value.strftime('%Y-%m-%d %H:%M:%S')
        elif t == IntField:
            return str(value)
        elif t == ListField:
            temp_res = "'%s'" % ','.join([str(el) for el in value])
            return trunc(temp_res, cls.LIST_MAX)
        elif t == EmbeddedDocumentField:
            temp_res =  "'%s'" % str(value)
            return trunc(temp_res, cls.EMBEDDED_MAX)
        elif t == BooleanField:
            return str(int(t))
        else:
            return "''"

    @classmethod
    def _mongo_val_2_sql(cls, value, t):
        db =get_dbcnn()
        return db.escape(cls._mongo_val_2_sql(value, t))

    @classmethod
    def update_one(cls, tb_name, fields, obj):
        values = ["'%s'" % str(obj.id)]
        colums = fields.keys()
        for k in colums:
            values.append(cls.mongo_val_2_sql(getattr(obj, k), fields[k]))
        upsert_sql = 'INSERT IGNORE INTO %s (%s) VALUES (%s);' % (tb_name, 'id, ' + ', '.join(colums), ', '.join(values))
        cls.execute(upsert_sql)

    @classmethod
    def update_tb(cls, c):
        tb_name = c.__name__
        create_name, t = cls._get_time_field(c)
        max_sql = 'SELECT MAX(%s) FROM %s;' % (create_name, tb_name)
        # print max_sql

        cond = cls.fetch_one(max_sql)
        if t == DateTimeField:
            if not cond:
                d = datetime.datetime(1, 1, 1, 0, 0, 0)
                cond = d

        elif not cond:
            if t == IntField:
                cond = 0

        fields = cls.table_fields(c)

        mongo_get = '%s.objects(%s__gte=%r).order_by(\'%s\').limit(%d)' % (tb_name, create_name, cond, create_name, cls.LIMIT_ROWS)
        print mongo_get
        try:
            mongo_res = eval(mongo_get)
            # mongo_res = [el for el in mongo_res]
        except:
            time.sleep(1)
            mongo_res = eval(mongo_get)
        colums = fields.keys()

        j = 1   # 用以多条合并成一个语句
        sqls = []
        for obj in mongo_res:
            cls.update_one(tb_name, colums, obj)
            # sqls.append(upsert_sql)
            # # print tb_name, colums, values
            # j += 1
            # if j == cls.UPSERT_MAX or i == res_len - 1:
            #     print sqls
            #     sql = '\n'.join(sqls)
            #     print sql
            #     cls.execute(sql)
            #     j = 1
            #     sqls = []
            #     #break

    @classmethod
    def run_all(cls):
        escape_tbs = ['TrackChat', 'UserMessage']
        for tb in cls.get_tables().values():
            tb_name = tb.__name__
            if tb_name in escape_tbs:
                continue
            try:
                cls.create_table(tb)
                cls.update_tb(tb)
                print '*' * 100
                print 'table: %s updated' % tb.__name__
            except Exception as e:
                print '!' * 100
                print 'table: %s Error' % tb.__name__, e
                continue


    @classmethod
    def c(cls):
        print dir(model)

# print MysqlSyncService.create_table(UserAddressList)
# print MysqlSyncService.update_tb(UserAddressList)