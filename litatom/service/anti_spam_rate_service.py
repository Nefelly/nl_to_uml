# coding: utf-8
import json
import time
import traceback
import logging
from ..const import (
    ONE_MIN,
    ONE_DAY,
    MAX_DIAMONDS
)
from ..error import (
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
    LEVEL_FIRST = 1
    LEVEL_SECCOND = 2
    LEVEL_STOP = 3

    '''
    5min  停止次数 及钻石数 
    WORD_KEY  超限后的提示语
    '''
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
                [5 * ONE_MIN, 2, 10],
                [ONE_DAY, 5, 500],
                [ONE_DAY, 10]
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
    def _get_error_message(cls, word, diamonds=None):
        res = FailedRateTooOften
        msg = GlobalizationService.get_region_word(word)
        res.update({'message': msg})
        if diamonds is not None:
            res.update({'diamonds': diamonds})
        return res

    @classmethod
    def get_key(cls, user_id, activity, level):
        user_interval_type_stop = '%s_%s_%d' % (user_id, activity, level)
        return REDIS_SPAMED.format(user_interval_type=user_interval_type_stop)

    @classmethod
    def out_of_times(cls, key, num):
        stop_num = redis_client.get(key)
        stop_num = 0 if not stop_num else int(stop_num)
        return stop_num > num

    @classmethod
    def judge_stop(cls, user_id, activity):


        def incr_key(key, interval):
            v = redis_client.incr(key)
            if v == 1:
                redis_client.expire(key, interval)

        info_m = cls.RATE_D.get(activity)
        if not info_m:
            return None, True
        first, second, final = info_m.get(cls.RATE_KEY)
        first_interval, first_stop, first_diamonds = first
        second_interval, second_stop, second_diamonds = second
        stop_interval, stop_num = final
        diamond_word, stop_word = info_m.get(cls.WORD_KEY)

        '''判断是否过期'''
        stop_key = cls.get_key(user_id, activity, cls.LEVEL_STOP)
        if cls.out_of_times(stop_key, stop_num):
            cls.inform_spam(user_id)
            return cls._get_error_message(stop_word), False

        second_key = cls.get_key(user_id, activity, cls.LEVEL_SECCOND)
        if cls.out_of_times(second_key, second_stop):
            cls.inform_spam(user_id)
            return cls._get_error_message(diamond_word, second_diamonds), False

        first_key = cls.get_key(user_id, activity, cls.LEVEL_FIRST)
        if cls.out_of_times(first_key, first_stop):
            cls.inform_spam(user_id)
            return cls._get_error_message(diamond_word, first_diamonds), False

        '''增加次数'''
        incr_key(first_key, first_interval)
        incr_key(second_key, second_interval)
        incr_key(stop_key, stop_interval)
        return None, True

    @classmethod
    def get_forbid_level(cls, user_id, activity):
        for el in [cls.LEVEL_STOP, cls.LEVEL_SECCOND, cls.LEVEL_FIRST]:
            key = cls.get_key(user_id, activity, el)
            num = cls.RATE_D.get(activity)[el - 1][1]
            if cls.out_of_times(key, num):
                return el
        return None

    @classmethod
    def how_much_should_pay(cls, user_id, activity):
        forbid_level = cls.get_forbid_level(user_id, activity)
        if forbid_level:
            if forbid_level == cls.LEVEL_STOP:
                return MAX_DIAMONDS
            return cls.RATE_D.get(activity)[forbid_level - 1][2]
        return 0

    @classmethod
    def reset_spam_type(cls, user_id, activity, diamonds=0):
        forbid_level = cls.get_forbid_level(user_id, activity)
        if forbid_level == cls.LEVEL_STOP:
            word = cls.RATE_D.get(activity)[cls.WORD_KEY][1]
            return cls._get_error_message(word), False
        redis_client.delete(cls.get_key(user_id, activity, cls.LEVEL_FIRST))
        if forbid_level == cls.LEVEL_SECCOND:
            redis_client.delete(cls.get_key(user_id, activity, cls.LEVEL_SECCOND))
        return None, True