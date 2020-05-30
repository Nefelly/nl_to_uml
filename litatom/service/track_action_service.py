# coding: utf-8
import time
import datetime
import cPickle
from flask import (
    request
)

from ..const import (
    USER_ACTION_EXCHANGE
)
from ..model import (
    UserAction
)
from ..key import (
    REDIS_LOC_USER_ACTIVE
)
from ..service import (
    MqService,
    AliLogService,
    GlobalizationService
)
from ..util import (
    now_date_key
)
from ..redis import RedisClient
volatile_redis = RedisClient()['volatile']


class TrackActionService(object):
    MQ_INSERT = False
    ALI_LOG_INSERT = True

    '''
    开启AIL_LOG_INSERT,则向ali log service中写入
    失败或未开启ali log insert，若开启MQ_INSERT，则向message queue中写user_action，
    message queue写入失败或者MQ_INSERT未开启，则向USER_ACTION表中直接写
    '''

    @classmethod
    def stat_active_user(cls, user_id, loc):
        if loc not in GlobalizationService.BIG_REGIONS.values():
            loc = GlobalizationService.LOC_EN
        key = REDIS_LOC_USER_ACTIVE.format(date_loc=now_date_key() + loc)
        volatile_redis.sadd(key, user_id)


    @classmethod
    def create_action(cls, user_id, action, other_user_id=None, amount=None, remark=None, version=None):
        if cls.ALI_LOG_INSERT:
            contents = [('user_id', user_id), ('session_id', request.session_id), ('location', request.loc), ('action', action)]
            cls.stat_active_user(user_id, request.loc)
            if other_user_id:
                contents += [('other_user_id', other_user_id)]
            if amount:
                contents += [('amount', str(amount))]
            if remark:
                contents += [('remark', remark)]
            if version:
                contents += [('version', version)]
            AliLogService.put_logs(contents)
        if cls.MQ_INSERT:
            if action not in ['match']:
                return True
            MqService.push(USER_ACTION_EXCHANGE,
                           {"args": cPickle.dumps(
                               [user_id, action, other_user_id, amount, remark, version, datetime.datetime.now(),
                                int(time.time())])}
                           # {
                           #         "user_id": user_id,
                           #         "action": action,
                           #         "other_user_id": other_user_id,
                           #         "amount": amount,
                           #         "remark": remark,
                           #         "create_time": cPickle.dumps(datetime.datetime.now())
                           # }
                           )
            return True
        return True
        # return cls._create_action(user_id, action, other_user_id, amount, remark, version)

    @classmethod
    def batch_create_client_track(cls, json_data):
        '''
        json_data
        [{u'path': u'/api/sns/v1/lit/home/online_users', u'code': 0, u'bytes': 2817, u'time': 125},
        {u'path': u'/api/sns/v1/lit/user/messages', u'code': 0, u'bytes': 93, u'time': 107},
        {u'path': u'/api/sns/v1/lit/user/query_online', u'code': 0, u'bytes': 110, u'time': 125}]
        :param user_id:
        :param action:
        :param other_user_id:
        :param amount:
        :param remark:
        :param version:
        :return:
        '''
        user_id = request.user_id if request.user_id else ''
        uuid = request.uuid if request.uuid else ''
        contents = []
        for el in json_data:
            raw = [('user_id', user_id), ('uuid', uuid), ('loc', request.loc), ('version', request.version)]
            for k in el:
                raw.append((k, str(el.get(k))))
            contents.append(raw)
        AliLogService.put_logs_batch(contents, project='client-track', logstore='client-track')
        return True

    @classmethod
    def pymongo_batch_insert(cls, collection, payload_list):
        insert_pack = []
        for el in payload_list:
            lst = cPickle.loads(str(el.get('args')))  # str  because mq encoded
            user_id, action, other_user_id, amount, remark, version, create_date, create_time = tuple(lst)
            # user_id = el.get('user_id')
            # action = el.get('action')
            # other_user_id = el.get('other_user_id')
            # amount = el.get('amount')
            # remark = el.get('remark')
            insert_pack.append({
                "action": action,
                "create_date": create_date,
                "create_time": create_time,
                "remark": remark,
                "other_user_id": other_user_id,
                "user_id": user_id,
                "version": version
            })
            # print insert_pack
        collection.insert_many(insert_pack, ordered=False)

    @classmethod
    def _create_action(cls, user_id, action, other_user_id=None, amount=None, remark=None, version=None):
        UserAction.create(user_id, action, other_user_id, amount, remark, version)
        return True

    @classmethod
    def action_by_uid(cls, user_id):
        '''
        :return uid: online map
        :param uids:
        :return:
        '''
        res = map(UserAction.to_json, UserAction.get_by_user_id(user_id))
        return res, True
