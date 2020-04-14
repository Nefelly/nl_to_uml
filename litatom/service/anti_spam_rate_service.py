# coding: utf-8
import json
import time
import traceback
import logging
from ..const import (
    ONE_MIN,
    ONE_DAY
)
from ..api.error import (
    FailedRateTooOften
)
from ..service import (
    GlobalizationService
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
    RATE_KEY = 'rate'
    WORD_KEY = 'word'
    LEVEL_FIRST = 0
    LEVEL_SECCOND = 1
    LEVEL_STOP = 2

    RATE_D = {
        ACCOST: {
            RATE_KEY: [
                [5 * ONE_MIN, 5, 10],
                [ONE_DAY, 30, 500],
                [ONE_DAY, 100]
            ],
            WORD_KEY: ['rate_conversation_diamonds', 'rate_conversation_stop']
        },
        FOLLOW:  {
            RATE_KEY: [
                [5 * ONE_MIN, 10, 10],
                [ONE_DAY, 50, 500],
                [ONE_DAY, 200]
            ],
            WORD_KEY: ['rate_follow_diamonds', 'rate_follow_stop']
        },
        COMMENT:  {
            RATE_KEY: [
                [5 * ONE_MIN, 10, 10],
                [ONE_DAY, 50, 500],
                [ONE_DAY, 100]
            ],
            WORD_KEY: ['rate_comment_diamonds', 'rate_commnet_stop']
        }
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
    def _get_error_message(cls, word):
        res = FailedRateTooOften
        msg = GlobalizationService.get_region_word(word)
        res.update({'message': msg})
        return res

    @classmethod
    def judge_stop(cls, user_id, activity):
        info_m = cls.RATE_D.get(activity)
        if not info_m:
            return None, True
        first, second, final = info_m.get(cls.RATE_KEY)
        first_interval, first_stop, first_diamonds = first
        second_interval, second_stop, second_diamonds = second
        diamond_word, stop_word = info_m.get(cls.WORD_KEY)

        user_interval_type_stop = '%s_%s_%d' % (user_id, activity, cls.LEVEL_STOP)
        stop_key = REDIS_SPAMED.format(user_interval_type=user_interval_type_stop)
        stop_num = redis_client.get(stop_key)
        stop_num = 0 if not stop_num else int(stop_num)
        stop_interval, stop_judge = final
        if stop_num >= stop_judge:
            return cls._get_error_message(stop_word), False


    @classmethod
    def reset_spam_type(cls, user_id, activity, ):
        pass