# coding: utf-8
import json
import time
import traceback
import logging
from ..const import (
    ONE_MIN,
    ONE_DAY
)
from ..key import (
    REDIS_SPAMED,
    SPAM_RATE_CONTROL
)

from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class AntiSpamRateService(object):
    '''

    '''
    ACCOST = 'accost'
    COMMENT = 'comment'
    FOLLOW = 'follow'


    RATE_D = {
        ACCOST: [
            [5 * ONE_MIN, 5, 10],
            [ONE_DAY, 30, 500],
            [ONE_DAY, 100]

        ],
        COMMENT: [
            [5 * ONE_MIN, ],
            [ONE_DAY, ],
            [ONE_DAY,]
        ],
        COMMENT: [
            [5 * ONE_MIN, ],
            [ONE_DAY, ],
            [ONE_DAY,]
        ],

    }

    @classmethod
    def inform_spam(cls, user_id):
        '''告知用户曾经被频控过'''
        key = REDIS_SPAMED.format(user_id=user_id)
        redis_client.set(key, 1, 3 * ONE_DAY)

    @classmethod
    def is_spamed_recent(cls, user_id):
        '''用户是否最近被频控'''
        key = REDIS_SPAMED.format(user_id=user_id)
        return redis_client.get(key) is None

    @classmethod
    def judge_stop(cls, user_id, activity):
        pass

    @classmethod
    def reset_spam_type(cls, user_id, activity, ):
        pass