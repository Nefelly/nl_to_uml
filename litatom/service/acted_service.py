# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    ActedRecord
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class ActedService(object):
    '''
    '''

    @classmethod
    def report_acted(cls, user_id, actions):
        for _ in actions:
            ActedRecord.create(user_id, _)
        return None, True

    @classmethod
    def acted_actions(cls, user_id):
        raw = {}
        for _ in ActedRecord.get_by_user_id(user_id):
            raw[_.content] = True
        return raw, True