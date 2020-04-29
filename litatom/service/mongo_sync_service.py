# coding: utf-8
import json
import time
import os
import traceback
import logging
from ..util import (
    get_args_from_db
)
from ..key import (
    REDIS_ALL_USER_ID_SET
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']
volatile_redis = RedisClient()['volatile']


class MongoSyncService(object):
    '''
    '''
    @classmethod
    def export_to_add(cls, db, table_name, db_name, fields=None):
        dir_name = '/tmp/'
        save_add = os.path.join(dir_name, '%s_%d.csv' % (table_name, int(time.time())))
        host, port, user, pwd, db, auth_db = get_args_from_db(db)
        if not fields:
            fields = 'user_id'
        else:
            fields = ','.join(fields)
        sql = '''mongoexport -h {host} --port {port} -u {user} -p {pwd} --authenticationDatabase {auth_db} -d {db_name} -c {collection} -f {fields} --type=csv --out {save_add}'''.format(
            host=host, port=port, user=user, pwd=pwd, auth_db=auth_db, db_name=db_name, collection=table_name, fields=fields, save_add=save_add)
        print sql
        os.system(sql)
        return save_add

    @classmethod
    def load_user_ids_to_redis(cls):
        db = 'DB_LIT'
        table_name = 'user_setting'
        db_name = 'lit'
        print time.time()
        save_add = cls.export_to_add(db, table_name, db_name)
        print 'loading succ', time.time()
        user_ids = open(save_add, 'r').read().strip().split('\n')[1:]
        print 'read succ', time.time()
        pp = volatile_redis.pipeline()
        for _ in user_ids:
            pp.sadd(REDIS_ALL_USER_ID_SET, _)
        pp.execute()
        print 'upload succ', time.time()
        print volatile_redis.scard(REDIS_ALL_USER_ID_SET)