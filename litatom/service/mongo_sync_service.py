# coding: utf-8
import json
import time
import os
import traceback
import logging
from ..util import (
    get_args_from_db
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']


class MongoSyncService(object):
    '''
    '''

    @classmethod
    def export_to_add(cls, db, table_name, db_name):
        dir_name = '/tmp/'
        save_add = os.path.join(dir_name, '%s_%d.csv' % (table_name, int(time.time())))
        host, port, user, pwd, db, auth_db = get_args_from_db(db)
        fields = 'user_id'
        sql = '''mongoexport -h {host} --port {port} -u {user} -p {pwd} --authenticationDatabase {auth_db} -d {db_name} -c {collection} -f {fields} --type=csv --out {save_add}'''.format(
            host=host, port=port, user=user, pwd=pwd, auth_db=auth_db, db_name=db_name, collection=table_name, fields=fields, save_add=save_add)
        print sql
        os.system(sql)
        return save_add

