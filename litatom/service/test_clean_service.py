# coding: utf-8
import json
import time
import traceback
import logging
from flask import (
    request
)
from ..service import (
    MongoSyncService,
    UserService,
    GlobalizationService,
    StatisticService
)
from ..model import *
from .. import model
from mongoengine import (
    NULLIFY,
    BooleanField,
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    ObjectIdField,
    ReferenceField,
    StringField,
    QuerySet,
    Q,
    ValidationError,
)
from ..const import (
    ONE_DAY
)
from hendrix.conf import setting
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class TestCleanService(object):
    '''
    '''
    MAINTAIN_TIME = 5 * ONE_DAY

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
    def get_old_users(cls):
        if not setting.IS_DEV:
            return u'you are not in testing', False
        user_ids = MongoSyncService.load_table_map(User, '_id')
        time_now = int(time.time())
        judge_time = time_now - cls.MAINTAIN_TIME
        res = []
        for _ in user_ids:
            region = GlobalizationService.get_region_by_user_id(_)
            if not region:
                print _, region, '!' * 100
            # GlobalizationService.set_current_region_for_script(region)
            request.region = region
            online_time = UserService.uid_online_time(_)
            if online_time < judge_time:
                res.append([_, time_now - online_time])
        ret = {
            'to_delete_num': len(res)
        }
        user_infos = StatisticService._user_infos_by_uids([el[0] for el in res])
        ret['users'] = user_infos
        return ret, True

    @classmethod
    def clean_model_field(cls):
        '''
        :return: {Report:['uid', 'target_uid']}
        '''
        models = cls.get_tables()
        fields = ['user_id', 'uid', 'target_uid']
        res = {}
        for model in models.values():
            res[model] =[]
            for _ in fields:
                if getattr(model, _, ''):
                    res[model].append(_)
        return res

    @classmethod
    def clear_old_users(cls):
        data, status = cls.get_old_users()
        if not status:
            return data, status
        user_ids = [el.get('user_id') for el in data.get('users')]
        users = map(User.get_by_id, user_ids)
        num = User.objects().count()
        return u'%d user left' % num, True


