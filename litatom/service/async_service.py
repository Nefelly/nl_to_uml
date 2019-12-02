# coding: utf-8
import json
import time
import traceback
import logging
from ..service import (
    MqService
)
import cPickle
from ..const import (
    COMMANDS_EXCHANGE
)
from ..service import (
    UserService
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class AsyncCmdService(object):
    '''
    '''
    BATCH_SEND = 'batch_send'
    @classmethod
    def push_msg(cls, cmd_type, args):
        payload = {
            'cmd_type': cmd_type,
            'args': cPickle.dumps(args)
        }
        MqService.push(COMMANDS_EXCHANGE, payload)
        return True

    @classmethod
    def execute(cls, payload):
        cmd_type = payload.get('cmd_type')
        args = payload.get('args')
        args = cPickle.loads(args)
        if cmd_type == cls.BATCH_SEND:
            UserService.msg_to_region_users(*args)