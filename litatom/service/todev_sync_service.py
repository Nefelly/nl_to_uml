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
    with switch_db(UserSetting, 'dev_lit') as UserSetting:
        print UserSetting.objects().count()