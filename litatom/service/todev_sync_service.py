# coding: utf-8
import json
import time
import traceback
from ..model import (
    UserSetting
)
import logging
from mongoengine.context_managers import switch_db
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class ToDevSyncService(object):
    '''
    '''
    @classmethod
    def test(cls):
        with switch_db(UserSetting, 'dev_lit') as UserSetting:
            print UserSetting.objects().count()

    @classmethod
    def sync(cls, model):
        dev_objs = []
        with switch_db(model, 'dev_lit') as Model:
            dev_objs = [el for el in  Model.objects()]
        return dev_objs