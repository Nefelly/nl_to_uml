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
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class AsyncCmdService(object):
    '''
    '''
    BATCH_SEND = 'batch_send'
    HUANXIN_SEND = 'huanxin_send'
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
        args = cPickle.loads(str(args))
        print cmd_type, args
        if cmd_type == cls.BATCH_SEND:
            from ..service import UserService
            UserService.msg_to_region_users(*args)
        elif cmd_type == cls.HUANXIN_SEND:
            from ..service import HuanxinService
            HuanxinService.batch_send_msgs(*args)
