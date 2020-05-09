# coding: utf-8
import json
import time
import os
import sys
import time
import datetime
import logging.handlers
import exceptions
import pymongo
import mongoengine
import bson
import cPickle
from hendrix.conf import setting
from pymongo import (
    ReplaceOne,
    uri_parser
)
import traceback
import logging
from ..model import *
from ..util import (
    get_args_from_db,
    ensure_path
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
    oplogs 同步  https://my.oschina.net/yagami1983/blog/807199
    '''

    @classmethod
    def get_args_from_alias(cls, model):
        '''
        ！！！！！！针对如relations这样的分片集群 不适用
        :param model:
        :return:

        '''
        model_meta = model._meta
        alias = model_meta['alias']
        m = mongoengine.connection._connection_settings.get(alias)
        if not m:
            m = mongoengine.connection._connection_settings.get('default')
        raw_host = m.get('host')[0]
        host_info_m = uri_parser.parse_uri(raw_host)
        host = host_info_m['nodelist'][0][0]
        port = m.get('port')
        user = m.get('username')
        pwd = m.get('password')
        db = m.get('name')
        auth_db = m.get('authentication_source')
        return host, port, user, pwd, db, auth_db, raw_host


    @classmethod
    def export_to_add(cls, model, fields=None):
        dir_name = '/tmp/'
        model_meta = model._meta
        table_name = model_meta['collection']
        save_add = os.path.join(dir_name, '%s_%d.csv' % (table_name, int(time.time())))
        host, port, user, pwd, db, auth_db, host_url = cls.get_args_from_alias(model)
        # host, port, user, pwd, db, auth_db = get_args_from_db(db)
        if not fields:
            fields = 'user_id'
        # else:
        #     fields = ','.join(fields)
        sql = '''mongoexport -h {host} --port {port} -u {user} -p {pwd} --authenticationDatabase {auth_db} -d {db_name} -c {collection} -f {fields} --type=csv --out {save_add}'''.format(
            host=host, port=port, user=user, pwd=pwd, auth_db=auth_db, db_name=db, collection=table_name, fields=fields, save_add=save_add)
        print sql
        os.system(sql)
        return save_add

    @classmethod
    def load_table_map(cls, model, key_field, wanted_fields=[]):
        if wanted_fields:
            fields = key_field + ',' + ','.join(wanted_fields)
        else:
            fields = key_field
        start = time.time()
        save_add = cls.export_to_add(model, fields)
        res_is_lst = False
        if len(wanted_fields) > 1:
            res_is_lst = True
        if wanted_fields:
            res = {}
        else:
            res = []
        read_head = False
        is_key_object = False if key_field != '_id' else True
        for l in open(save_add).readlines():
            if not read_head:
                read_head = True
                continue
            l = l.strip()
            tmp_fields = l.split(',')
            parse_len = len('ObjectId(')
            'ObjectId(5ca2b5013fff224462b40965)'
            if is_key_object:
                tmp_fields[0] = tmp_fields[0][parse_len:-1]
            if not wanted_fields:
                res.append(tmp_fields[0])
            else:
                if res_is_lst:
                    res[tmp_fields[0]] = tmp_fields[1:]
                else:
                    res[tmp_fields[0]] = tmp_fields[1]
        os.remove(save_add)
        print 'read succ using:', time.time() - start
        return res

    # @classmethod
    # def load_user_setting_map(cls, wanted_fileds=[]):
    #     db = 'DB_LIT'
    #     table_name = 'user_setting'
    #     db_name = 'lit'
    #     fields = 'user_id,' + ','.join(wanted_fileds)
    #     save_add = cls.export_to_add(db, table_name, db_name, fields)
    #     res_is_lst = False
    #     if len(wanted_fileds) > 1:
    #         res_is_lst = True
    #     if wanted_fileds:
    #         res = {}
    #     else:
    #         res = []
    #     for l in open(save_add).readlines():
    #         if not wanted_fileds:
    #             res.append(l)
    #         else:
    #             tmp_fields = l.split(',')
    #             if res_is_lst:
    #                 res[tmp_fields[0]] = tmp_fields[1:]
    #             else:
    #                 res[tmp_fields[0]] = tmp_fields[1]
    #     # os.remove(save_add)
    #     return res

    @classmethod
    def load_user_ids_to_redis(cls):
        # db = 'DB_LIT'
        # table_name = 'user_setting'
        # db_name = 'lit'
        # save_add = cls.export_to_add(db, table_name, db_name)
        # print 'loading succ', time.time()
        # user_ids = open(save_add, 'r').read().strip().split('\n')[1:]
        user_ids = cls.load_table_map(User, '_id')
        pp = volatile_redis.pipeline()
        for _ in user_ids:
            pp.sadd(REDIS_ALL_USER_ID_SET, _)
        volatile_redis.delete(REDIS_ALL_USER_ID_SET)
        pp.execute()
        print 'upload succ', time.time()
        print volatile_redis.scard(REDIS_ALL_USER_ID_SET)

    @classmethod
    def real_time_sync_userids(cls):
        cls.load_user_ids_to_redis()
        timestamp_save_add = '/data/tmp/userid_sync.time'
        ensure_path(timestamp_save_add)
        host, port, user, pwd, db, auth_db, host_url = cls.get_args_from_alias(User)
        user_collection_name = User._meta['collection']
        res = {}
        def sync_oplog(oplog):
            op = oplog['op']  # 'n' or 'i' or 'u' or 'c' or 'd'
            ns = oplog['ns']
            dbname, collname = ns.split('.', 2)
            db = 'lit'
            if dbname != db or collname != user_collection_name:
                return
            # if not res.get(op):
            #     res[op] = 1
            #     print oplog
            if op == 'i':  # insert
                user_id = str(oplog['o'].get('_id'))
                print user_id, '!' * 50
                volatile_redis.sadd(REDIS_ALL_USER_ID_SET, user_id)
                # self._dst_mc[dbname][collname].replace_one({'_id': oplog['o']['_id']}, oplog['o'], upsert=True)
            elif op == 'u':  # update
                pass
            elif op == 'd':  # delete
                user_id = str(oplog['o'].get('_id'))
                print user_id, '!' * 50
                volatile_redis.srem(REDIS_ALL_USER_ID_SET, user_id)
            elif op == 'c':  # command
                pass
            elif op == 'n':  # no-op
                pass
            else:
               print('unknown operation: %s' % oplog)
        opsync_obj = OplogSyncService(host_url, port, timestamp_save_add=timestamp_save_add)
        opsync_obj.sync(sync_oplog)


class OplogSyncService(object):
    '''
    oplog 的样子
    {u'h': 3887152545823678239L, u'ts': Timestamp(1588428334, 1), u'o': {u'$set': {u'total_match_inter': 56066.90000000002, u'match_times': 885}}, u't': 141L, u'v': 2, u'ns': u'lit.user_model', u'o2': {u'_id': ObjectId('5e2b880e3fff226a6e5e9fa8')}, u'op': u'u'}
    {u'h': 1691073658577699620L, u'ts': Timestamp(1588428334, 5), u'o': {u'_id': ObjectId('5ead7e2b044e0857078b4690')}, u't': 141L, u'v': 2, u'ns': u'lit.follow', u'op': u'd'}
    {u'h': 1530092034340961366L, u'ts': Timestamp(1588428334, 10), u'o': {u'user_id': u'5e47a73c3fff2264fe7ee816', u'money': 0.0, u'create_time': datetime.datetime(2020, 5, 2, 22, 5, 34, 126000), u'diamonds': 1, u'action': u'add_by_activity', u'_id': ObjectId('5ead7e2e3fff22584ef9ffe3')}, u't': 141L, u'v': 2, u'ns': u'lit.account_flow_record', u'op': u'i'}

    '''
    def __init__(self, src_host, src_port, **kwargs):
        self._src_host = src_host
        self._src_port = src_port
        self._start_optime = None  # if true, only sync oplog
        self._last_optime = None  # optime of the last oplog has been replayed
        self.timestamp_save_add = kwargs.get('timestamp_save_add', '')
        self._load_timestamp()
        self._src_mc = pymongo.MongoClient(src_host, src_port)

    def get_default_timestamp(self):
        self._start_optime = bson.timestamp.Timestamp(int(time.time()), 0)

    def _load_timestamp(self):
        if self.timestamp_save_add and os.path.exists(self.timestamp_save_add):
            time_str = open(self.timestamp_save_add).read()
            self._start_optime = cPickle.loads(time_str)
        else:
            self.get_default_timestamp()

    @classmethod
    def print_msg(cls, msg):
        print msg

    def sync(self, func, **args):
        if self._start_optime:
            self.print_msg("locating oplog, it will take a while")
            self.print_msg('start timestamp is %s actually' % self._start_optime)
            self._last_optime = self._start_optime
            self._sync_oplog(func, *args)

    def _sync_oplog(self, func, *args):
        """ Replay oplog.
        """
        try:
            host, port = self._src_mc.address
            self.print_msg('try to sync oplog from %s on %s:%d' % (self._start_optime, host, port))
            cursor = self._src_mc['local']['oplog.rs'].find({'ts': {'$gte': self._start_optime}}, cursor_type=pymongo.cursor.CursorType.TAILABLE, no_cursor_timeout=True)
            #Tailable cursors are only for use with capped collections.
            if cursor[0]['ts'].time != self._start_optime.time:
                self.print_msg('%s is stale, terminate' % self._start_optime)
                return
        except IndexError as e:
            self.print_msg(e)
            self.print_msg('%s not found, terminate' % self._start_optime)
            return
        except Exception as e:
            self.print_msg(e)
            raise e

        self.print_msg('replaying oplog')
        n_replayed = 0
        while True:
            try:
                if not cursor.alive:
                    self.print_msg('cursor is dead')
                    raise pymongo.errors.AutoReconnect

                # get an oplog
                oplog = cursor.next()
                func(oplog, *args)
                self._last_optime = oplog['ts']
                n_replayed += 1
                # if n_replayed % 1000 == 0:
                #     self._print_progress(oplog)
            except StopIteration as e:
                # there is no oplog to replay now, wait a moment
                time.sleep(0.1)
            except pymongo.errors.AutoReconnect:
                self._src_mc.close()
                self._src_mc = pymongo.MongoClient(self._src_host, self._src_port)
                cursor = self._src_mc['local']['oplog.rs'].find({'ts': {'$gte': self._last_optime}}, cursor_type=pymongo.cursor.CursorType.TAILABLE, no_cursor_timeout=True)
                if cursor[0]['ts'] != self._last_optime:
                    self._logger.error('%s is stale, terminate' % self._last_optime)
                    return


class MongoSynchronizer(object):
    """ MongoDB multi-source synchronizer.
    """
    def __init__(self, src_hostportstr, dst_hostportstr, **kwargs):
        """ Constructor.
        """
        if not src_hostportstr:
            raise Exception('src hostportstr is empty')
        if not dst_hostportstr:
            raise Exception('dst hostportstr is empty')

        self._src_hostportstr = src_hostportstr
        self._dst_hostportstr = dst_hostportstr
        self._src_mc = None
        self._dst_mc = None
        self._start_optime = None # if true, only sync oplog
        self._last_optime = None # optime of the last oplog has been replayed
        self._logger = logging.getLogger()
        self._start_optime = kwargs.get('start_optime')

        self._src_mc = pymongo.MongoClient(src_hostportstr)

        self._dst_mc = pymongo.MongoClient(dst_hostportstr)

    def __del__(self):
        """ Destructor.
        """
        if self._src_mc:
            self._src_mc.close()
        if self._dst_mc:
            self._dst_mc.close()

    def _sync(self):
        """ Sync databases and oplog.
        """
        if self._start_optime:
            self._logger.info("locating oplog, it will take a while")
            oplog_start = bson.timestamp.Timestamp(int(self._start_optime), 0)
            doc = self._src_mc['local']['oplog.rs'].find_one({'ts': {'$gte': oplog_start}})
            if not doc:
                self._logger.error('specified oplog not found')
                return
            oplog_start = doc['ts']
            self._logger.info('start timestamp is %s actually' % oplog_start)
            self._last_optime = oplog_start
            self._sync_oplog(oplog_start)


    def _sync_oplog(self, oplog_start):
        """ Replay oplog.
        """
        try:
            host, port = self._src_mc.address
            self._logger.info('try to sync oplog from %s on %s:%d' % (oplog_start, host, port))
            cursor = self._src_mc['local']['oplog.rs'].find({'ts': {'$gte': oplog_start}}, cursor_type=pymongo.cursor.CursorType.TAILABLE, no_cursor_timeout=True)
            #Tailable cursors are only for use with capped collections.
            if cursor[0]['ts'] != oplog_start:
                self._logger.error('%s is stale, terminate' % oplog_start)
                return
        except IndexError as e:
            self._logger.error(e)
            self._logger.error('%s not found, terminate' % oplog_start)
            return
        except Exception as e:
            self._logger.error(e)
            raise e

        self._logger.info('replaying oplog')
        n_replayed = 0
        while True:
            try:
                if not cursor.alive:
                    self._logger.error('cursor is dead')
                    raise pymongo.errors.AutoReconnect

                # get an oplog
                oplog = cursor.next()

                # guarantee that replay oplog successfully
                recovered = False
                while True:
                    try:
                        if recovered:
                            self._logger.info('recovered at %s' % oplog['ts'])
                            recovered = False
                        self._replay_oplog(oplog)
                        n_replayed += 1
                        if n_replayed % 1000 == 0:
                            self._print_progress(oplog)
                        break
                    except pymongo.errors.DuplicateKeyError as e:
                        # TODO
                        # through unique index, delete old, insert new
                        #self._logger.error(oplog)
                        #self._logger.error(e)
                        break
                    except pymongo.errors.OperationFailure as e:
                        # TODO
                        # through unique index, delete old, insert new
                        #self._logger.error(oplog)
                        #self._logger.error(e)
                        break
                    except pymongo.errors.AutoReconnect as e:
                        self._logger.error(e)
                        self._logger.error('interrupted at %s' % oplog['ts'])
                        self._dst_mc = pymongo.MongoClient(self._dst_hostportstr)
                        if self._dst_mc:
                            recovered = True
                    except pymongo.errors.WriteError as e:
                        self._logger.error(e)
                        self._logger.error('interrupted at %s' % oplog['ts'])
                        self._dst_mc = pymongo.MongoClient(self._dst_hostportstr)
                        if self._dst_mc:
                            recovered = True
            except StopIteration as e:
                # there is no oplog to replay now, wait a moment
                time.sleep(0.1)
            except pymongo.errors.AutoReconnect:
                self._src_mc.close()
                self._src_mc = pymongo.MongoClient(self._src_hostportstr)
                cursor = self._src_mc['local']['oplog.rs'].find({'ts': {'$gte': self._last_optime}}, cursor_type=pymongo.cursor.CursorType.TAILABLE, no_cursor_timeout=True)
                if cursor[0]['ts'] != self._last_optime:
                    self._logger.error('%s is stale, terminate' % self._last_optime)
                    return

    def _replay_oplog(self, oplog):
       self._replay_oplog_mongodb(oplog)

    def _print_progress(self, oplog):
        ts = oplog['ts']
        self._logger.info('sync to %s, %s' % (datetime.datetime.fromtimestamp(ts.time), ts))

    def _replay_oplog_mongodb(self, oplog):
        # Replay oplog on destination if source is MongoDB.
        # parse
        ts = oplog['ts']
        op = oplog['op'] # 'n' or 'i' or 'u' or 'c' or 'd'
        ns = oplog['ns']
        dbname = ns.split('.', 1)[0]
        if op == 'i': # insert
            collname = ns.split('.', 1)[1]
            self._dst_mc[dbname][collname].insert_one(oplog['o'])
            # self._dst_mc[dbname][collname].replace_one({'_id': oplog['o']['_id']}, oplog['o'], upsert=True)
        elif op == 'u': # update
            collname = ns.split('.', 1)[1]
            self._dst_mc[dbname][collname].update(oplog['o2'], oplog['o'])
        elif op == 'd': # delete
            collname = ns.split('.', 1)[1]
            self._dst_mc[dbname][collname].delete_one(oplog['o'])
        elif op == 'c': # command
            self._dst_mc[dbname].command(oplog['o'])
        elif op == 'n': # no-op
            pass
        else:
            self._logger.error('unknown operation: %s' % oplog)
        self._last_optime = ts

    def run(self):
        """ Start data synchronization.
        """
        # never drop database automatically
        # you should clear the databases manually if necessary
        try:
            self._sync()
        except exceptions.KeyboardInterrupt:
            self._logger.info('terminating')

def logger_init(filepath):
    """ Init logger for global.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    if filepath:
        handler_log = logging.handlers.RotatingFileHandler(filepath, mode='a', maxBytes=1024*1024*100, backupCount=3)
        handler_log.setFormatter(formatter)
        handler_log.setLevel(logging.INFO)
        logger.addHandler(handler_log)
    else:
        handler_stdout = logging.StreamHandler(sys.stdout)
        handler_stdout.setFormatter(formatter)
        handler_stdout.setLevel(logging.INFO)
        logger.addHandler(handler_stdout)

def main():
    logger_init(config.cf.get('conf', 'log'))
    syncer = MongoSynchronizer(
            config.cf.get('db', 'mongo_f_uri'),
            config.cf.get('db', 'mongo_t_uri'),
            start_optime=config.cf.get('conf', 'start_time'))
    syncer.run()

if __name__ == '__main__':
    main()