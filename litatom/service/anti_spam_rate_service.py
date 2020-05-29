# coding: utf-8
import json
import time
import traceback
import logging
from hendrix.conf import setting
from ..const import (
    ONE_MIN,
    ONE_DAY,
    MAX_DIAMONDS
)
from flask import (
    request
)
from ..error import (
    FailedRateTooOften
)
from ..service import (
    GlobalizationService,
    AliLogService
)
from ..key import (
    REDIS_SPAMED,
    REDIS_SPAM_RATE_CONTROL,
    REDIS_PROTECT_RATE_CONTROL,
    REDIS_SPAMED_INFORMED,
    REDIS_RATE_VISITED
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
    TIME_TO_LIVE = ONE_DAY
    EVER_SPAMED = 3 * ONE_DAY

    '''
    5min  停止次数 及钻石数 
    WORD_KEY  超限后的提示语
    '''
    RATE_D = {
        ACCOST: {
            RATE_KEY: [
                [5 * ONE_MIN, 5, 1],
                [ONE_DAY, 30, 50],
                [ONE_DAY, 100]
            ],
            WORD_KEY: ['rate_conversation_diamonds', 'rate_conversation_stop']
        },
        FOLLOW: {
            RATE_KEY: [
                [5 * ONE_MIN, 10, 1],
                [ONE_DAY, 50, 50],
                [ONE_DAY, 200]
            ],
            WORD_KEY: ['rate_follow_diamonds', 'rate_follow_stop']
        },
        COMMENT: {
            RATE_KEY: [
                [5 * ONE_MIN, 10, 1],
                [ONE_DAY, 50, 50],
                [ONE_DAY, 100]
            ],
            WORD_KEY: ['rate_comment_diamonds', 'rate_comment_stop']
        }
    }

    PROTECTED_D = {
        ACCOST: {
            RATE_KEY: [
                [5 * ONE_MIN, 5, 5],
                [ONE_DAY, 100, 5],
                [ONE_DAY, 10000]
            ],
            WORD_KEY: 'protected_conversation_diamonds'
        }
    }

    if setting.IS_DEV:
        RATE_D = {
            ACCOST: {
                RATE_KEY: [
                    [5 * ONE_MIN, 2, 10],
                    [ONE_DAY, 3, 500],
                    [ONE_DAY, 10]
                ],
                WORD_KEY: ['rate_conversation_diamonds', 'rate_conversation_stop']
            },
            FOLLOW: {
                RATE_KEY: [
                    [2 * ONE_MIN, 4, 10],
                    [ONE_DAY, 8, 500],
                    [ONE_DAY, 10]
                ],
                WORD_KEY: ['rate_follow_diamonds', 'rate_follow_stop']
            },
            COMMENT: {
                RATE_KEY: [
                    [5 * ONE_MIN, 4, 10],
                    [ONE_DAY, 8, 500],
                    [ONE_DAY, 10]
                ],
                WORD_KEY: ['rate_comment_diamonds', 'rate_comment_stop']
            }
        }

    @classmethod
    def inform_spam(cls, user_id, activity=None):
        '''告知用户曾经被频控过'''
        key = REDIS_SPAMED.format(user_id=user_id)
        redis_client.set(key, 1, cls.EVER_SPAMED)
        if activity:
            spam_informed_key = REDIS_SPAMED_INFORMED.format(user_id_activity=user_id + activity)
            if not redis_client.get(spam_informed_key):
                cls.record_over(user_id, activity, 0)
                redis_client.set(spam_informed_key, 1, cls.EVER_SPAMED)

    @classmethod
    def is_spamed_recent(cls, user_id):
        '''用户是否最近被频控'''
        key = REDIS_SPAMED.format(user_id=user_id)
        return redis_client.get(key) is None

    @classmethod
    def _get_error_message(cls, word, activity, diamonds=None):
        msg = GlobalizationService.get_region_word(word)
        if diamonds is None:
            return msg
        res = FailedRateTooOften
        res.update({'message': msg, 'activity': activity})
        if diamonds is not None:
            res.update({'diamonds': diamonds})
        return res

    @classmethod
    def _get_protected_error_message(cls, word, activity, other_id, diamonds=None):
        res = cls._get_error_message(word, activity, diamonds)
        if isinstance(res, dict):
            res['other_info'] = other_id
        return res

    @classmethod
    def get_key(cls, user_id, activity, level, is_protected=False):
        user_interval_type_stop = '%s_%s_%d' % (user_id, activity, level)
        raw_key = REDIS_SPAM_RATE_CONTROL if not is_protected else REDIS_PROTECT_RATE_CONTROL
        return raw_key.format(user_interval_type=user_interval_type_stop)

    @classmethod
    def out_of_times(cls, key, num):
        stop_num = redis_client.get(key)
        stop_num = 0 if not stop_num else int(stop_num)
        ''' 先判断 再往上加的  所以第二次 stop_num 为 1 第三次 为 2'''
        return stop_num >= num

    @classmethod
    def just_out_times(cls, key, num):
        stop_num = redis_client.get(key)
        stop_num = 0 if not stop_num else int(stop_num)
        ''' 先判断 再往上加的  所以第二次 stop_num 为 1 第三次 为 2'''
        return stop_num == num

    @classmethod
    def _visit_before_key(cls, user_id, activity, other_id):
        return REDIS_RATE_VISITED.format(user_id_activity_other_id='%s_%s_%s' % (user_id, activity, other_id))

    @classmethod
    def is_protected_visit_before(cls, user_id, activity, other_id):
        key = cls._visit_before_key(user_id, activity, other_id)
        if redis_client.get(key):
            return True
        return False

    @classmethod
    def set_protected_visit_before(cls, user_id, activity, other_id):
        '''
        被保护用户的多次搭讪仅记做一次
        :param user_id:
        :param activity:
        :param other_id:
        :return:
        '''
        key = cls._visit_before_key(user_id, activity, other_id)
        redis_client.incr(key)
        redis_client.expire(key, cls.TIME_TO_LIVE)

    @classmethod
    def del_protected_visit_before(cls, user_id, activity, other_id):
        '''
        被保护用户的多次搭讪仅记做一次
        :param user_id:
        :param activity:
        :param other_id:
        :return:
        '''
        key = cls._visit_before_key(user_id, activity, other_id)
        redis_client.delete(key)

    @classmethod
    def should_not_be_protected(cls, other_id, activity):
        '''
        判断这个id对应的活动是否应该被限流以保护
        :param other_id:
        :param avtivity:
        :return:
        '''

        info_m = cls.PROTECTED_D.get(activity)
        if not info_m:
            return None, True

        first, second, final = info_m.get(cls.RATE_KEY)
        first_interval, first_stop, first_diamonds = first
        second_interval, second_stop, second_diamonds = second
        diamond_word = info_m.get(cls.WORD_KEY)

        second_key = cls.get_key(other_id, activity, cls.LEVEL_SECCOND, True)
        if cls.out_of_times(second_key, second_stop):
            return cls._get_protected_error_message(diamond_word, activity, other_id, second_diamonds), False

        first_key = cls.get_key(other_id, activity, cls.LEVEL_FIRST, True)
        if cls.out_of_times(first_key, first_stop):
            return cls._get_protected_error_message(diamond_word, activity, other_id, first_diamonds), False

        '''增加次数'''
        cls.incr_key(first_key, first_interval)
        cls.incr_key(second_key, second_interval)
        return None, True

    @classmethod
    def incr_key(cls, key, interval):
        v = redis_client.incr(key)
        if v == 1:
            redis_client.expire(key, interval)

    @classmethod
    def judge_stop(cls, user_id, activity, other_id=None, related_protcted=False, other_protected=False):
        '''
        判断用户是否要被频控，
        :param user_id:
        :param activity:
        :param other_id:
        :param related_protcted: 用来防止对一个id进行多次频控 多次重复 只会计算一个
        :param other_protected:  另外的id所代表的是否要被频控；
        :return:
        '''
        if related_protcted:
            if other_id:
                if cls.is_protected_visit_before(user_id, activity, other_id):
                    return None, True

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
            '''多次尝试 只记录一次'''
            if cls.just_out_times(stop_key, stop_num):
                cls.record_over(user_id, activity, cls.LEVEL_FIRST)
                cls.incr_key(stop_key, stop_interval)
            return cls._get_error_message(stop_word, activity), False

        second_key = cls.get_key(user_id, activity, cls.LEVEL_SECCOND)
        if cls.out_of_times(second_key, second_stop):
            cls.inform_spam(user_id)
            if cls.just_out_times(second_key, second_stop):
                cls.record_over(user_id, activity, cls.LEVEL_SECCOND)
                cls.incr_key(second_key, second_interval)
            return cls._get_error_message(diamond_word, activity, second_diamonds), False

        first_key = cls.get_key(user_id, activity, cls.LEVEL_FIRST)
        if cls.out_of_times(first_key, first_stop):
            cls.inform_spam(user_id)
            if cls.just_out_times(first_key, first_stop):
                cls.record_over(user_id, activity, cls.LEVEL_FIRST)
                cls.incr_key(first_key, first_interval)
            return cls._get_error_message(diamond_word, activity, first_diamonds), False

        '''增加次数'''
        cls.incr_key(first_key, first_interval)
        cls.incr_key(second_key, second_interval)
        cls.incr_key(stop_key, stop_interval)
        if related_protcted:
            cls.set_protected_visit_before(user_id, activity, other_id)
            if other_protected:
                data, status = cls.should_not_be_protected(other_id, activity)
                if not status:
                    cls.del_protected_visit_before(user_id, activity, other_id)
                    redis_client.decr(first_key)
                    redis_client.decr(second_key)
                    redis_client.decr(stop_key)
                    return data, False
        if activity == cls.ACCOST:
            cls.record_accost(user_id, other_id)
        return None, True

    @classmethod
    def get_forbid_level(cls, user_id, activity, other_id=''):
        m = cls.PROTECTED_D if other_id else cls.RATE_D
        check_id = other_id if other_id else user_id
        is_protected = True if other_id else False
        for el in [cls.LEVEL_STOP, cls.LEVEL_SECCOND, cls.LEVEL_FIRST]:
            key = cls.get_key(check_id, activity, el, is_protected)
            if not m.get(activity):
                m = cls.RATE_D
            num = m.get(activity).get(cls.RATE_KEY)[el - 1][1]
            if cls.out_of_times(key, num):
                return el
        return None

    @classmethod
    def how_much_should_pay(cls, user_id, activity, other_id):
        m = cls.PROTECTED_D if other_id else cls.RATE_D
        if not m.get(activity):
            other_id = ''
            m = cls.RATE_D
        check_id = other_id if other_id else user_id
        forbid_level = cls.get_forbid_level(check_id, activity, other_id)
        if forbid_level:
            if forbid_level == cls.LEVEL_STOP:
                return MAX_DIAMONDS
            # m = cls.PROTECTED_D if other_id else cls.RATE_D
            return m.get(activity).get(cls.RATE_KEY)[forbid_level - 1][2]
        if other_id:
            return cls.how_much_should_pay(user_id, activity, '')
        return 0

    @classmethod
    def remove_keys(cls, user_id):
        for _ in [cls.ACCOST, cls.COMMENT, cls.FOLLOW]:
            for l in [cls.LEVEL_STOP, cls.LEVEL_SECCOND, cls.LEVEL_FIRST]:
                redis_client.delete(cls.get_key(user_id, _, l))

    @classmethod
    def reset_spam_type(cls, user_id, activity, other_id=None):
        if other_id:
            ''' 针对他人的频控保护'''
            cls.set_protected_visit_before(user_id, activity, other_id)
            return None, True
        forbid_level = cls.get_forbid_level(user_id, activity)
        if forbid_level == cls.LEVEL_STOP:
            word = cls.RATE_D.get(activity)[cls.WORD_KEY][1]
            return cls._get_error_message(word), False
        # cls.record_over(user_id, activity, forbid_level, request.loc, request.version, reset = True)
        redis_client.delete(cls.get_key(user_id, activity, cls.LEVEL_FIRST))
        if forbid_level == cls.LEVEL_SECCOND:
            ''' 如果要第一级不清空 应该另外做判断'''
            redis_client.delete(cls.get_key(user_id, activity, cls.LEVEL_SECCOND))
        return None, True

    @classmethod
    def record_over(cls, user_id, activity, stop_level, reset=False):
        loc = '' if not request.loc else request.loc
        version = '' if not request.version else request.version
        if reset:
            activity = '%s_%s' % (activity, 'reset')
        contents = [('action', 'spam_rate_control'), ('location', loc), ('user_id', str(user_id)), ('version', version),
                    ('activity_level', '%s_%d' % (activity, stop_level))]
        AliLogService.put_logs(contents)

    @classmethod
    def record_accost(cls, user_id, other_user_id):
        loc = '' if not request.loc else request.loc
        version = '' if not request.version else request.version
        session_id = '' if not request.session else request.session
        contents = [('action', 'accost'), ('other_user_id', other_user_id), ('location', loc),
                    ('remark', 'accost_pass'), ('session_id', str(session_id)),
                    ('user_id', str(user_id)), ('version', version)]
        AliLogService.put_logs(contents)