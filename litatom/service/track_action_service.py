# coding: utf-8
import time
import datetime
import cPickle
from ..const import (
    USER_ACTION_EXCHANGE
)
from ..model import (
    UserAction
)
from ..service import (
    MqService,
    AliLogService
)

class TrackActionService(object):
    MQ_INSERT = True
    ALI_LOG_INSERT = False

    '''
    开启AIL_LOG_INSERT,则向ali log service中写入
    失败或未开启ali log insert，若开启MQ_INSERT，则向message queue中写user_action，
    message queue写入失败或者MQ_INSERT未开启，则向USER_ACTION表中直接写
    '''
    @classmethod
    def create_action(cls, user_id, sid, action, other_user_id=None, amount=None, remark=None, version=None):
        if cls.ALI_LOG_INSERT:
            contents=[('user_id',user_id), ('session_id', sid), ('action',action), ('other_user_id',other_user_id),
                      ('amount',amount), ('remark',remark),('version',version)]
            return AliLogService.put_logs(contents).get_all_headers()
        if cls.MQ_INSERT:
            MqService.push(USER_ACTION_EXCHANGE,
                           {"args": cPickle.dumps([user_id, action, other_user_id, amount, remark, version, datetime.datetime.now(), int(time.time())])}
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
        return cls._create_action(user_id, action, other_user_id, amount, remark, version)

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

    @classmethod
    def write_to_alilogservice(cls,user_id, action, other_user_id, amount=None, remark=None, version=None):

