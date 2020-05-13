# coding: utf-8
import json
import time
import traceback
import logging
from ..service import (
    MongoSyncService,
    UserService,
    GlobalizationService,
    MysqlSyncService
)
from ..model import (
    User
)
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
    def get_old_users(cls):
        if not setting.IS_DEV:
            return u'you are not in testing', False
        user_ids = MongoSyncService.load_table_map(User, '_id')
        time_now = int(time.time())
        judge_time = time_now - cls.MAINTAIN_TIME
        res = []
        print 'user_ids to check', len(user_ids)
        for _ in user_ids:
            region = GlobalizationService.get_region_by_user_id(_)
            GlobalizationService.set_current_region_for_script(region)
            online_time = UserService.uid_online(_)
            if online_time < judge_time:
                res.append([_, time_now - online_time])
        ret = {
            'to_delete_num': len(res)
        }
        user_infos = UserService._user_infos_by_uids([el[0] for el in res])
        ret['users'] = user_infos
        return ret, True

    @classmethod
    def clean_model_field(cls):
        models = MysqlSyncService.get_tables()

    @classmethod
    def clear_old_users(cls):
        data, status = cls.get_old_users()
        if not status:
            return data, status
        user_ids =

