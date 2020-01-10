# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    UserAccount,
    AccountFlowRecord
)
from ..const import (
    ONE_WEEK
)
from ..service import (
    MatchService,
    AnoyMatchService,
    VoiceMatchService,
    VideoMatchService,
    AntiSpamService,
    PalmService
)
from ..redis import RedisClient
from flask import (
    request
)

logger = logging.getLogger(__name__)
redis_client = RedisClient()['lit']


class AccountService(object):
    '''
    '''
    WEEK_MEMBER = 'week_member'
    ONE_MORE_TIME = 'one_more_time'
    ACCELERATE = 'accelerate'
    ACCOST_RESET = 'accost_reset'
    PALM_RESULT = 'palm_result'
    PRODUCT_INFOS = {
        WEEK_MEMBER: 15,
        ONE_MORE_TIME: 1,
        ACCELERATE: 1,
        ACCOST_RESET: 10,
        PALM_RESULT: 10
    }
    SHARE = 'share'
    WATCH_AD = 'watch_video'
    PAY_ACTIVITIES = {
        SHARE: 10,
        WATCH_AD: 5
    }

    MEMBER_SHIPS = [WEEK_MEMBER]
    ERR_DIAMONDS_NOT_ENOUGH = 'not enough diamonds, please deposit first.'

    @classmethod
    def diamond_products(cls, user_id):
        return {
            '10diamonds': 10,
            'asfd324': 5,
            '324asd': 15
        }, True

    @classmethod
    def get_user_account_info(cls, user_id):
        return UserAccount.get_account_info(user_id)

    @classmethod
    def change_diamonds(cls, user_id, diamonds):
        user_account = UserAccount.get_by_user_id(user_id)
        if not user_account:
            user_account = UserAccount.create_account(user_id)
        if diamonds >= 0:
            user_account.diamonds += diamonds
            user_account.save()
            return None
        else:
            if user_account.diamonds + diamonds >= 0:
                user_account.diamonds += diamonds
                user_account.save()
                return None
            return cls.ERR_DIAMONDS_NOT_ENOUGH

    @classmethod
    def is_member(cls, user_id):
        user_account = UserAccount.get_by_user_id(user_id)
        if not user_account:
            return False
        time_now = int(time.time())
        if user_account.membership_time > time_now:
            return True
        return False

    @classmethod
    def buy_member_ship(cls, user_id, member_type=WEEK_MEMBER):
        user_account = UserAccount.get_by_user_id(user_id)
        if not user_account:
            return u'user account not exists'
        old_membership_time = user_account.membership_time
        time_now = int(time.time())
        if old_membership_time < time_now:
            old_membership_time = time_now
        if member_type == cls.WEEK_MEMBER:
            user_account.membership_time = old_membership_time + ONE_WEEK
            user_account.save()
        # MatchService.set_member_match_left(user_id)
        return None

    @classmethod
    def buy_product(cls, user_id, product):
        if product not in cls.PRODUCT_INFOS:
            return u'product must be one of: %s' % (','.join(cls.PRODUCT_INFOS.keys())), False
        diamonds = cls.PRODUCT_INFOS.get(product)
        if product in cls.MEMBER_SHIPS:
            err_msg = cls.buy_member_ship(user_id, product)
            if err_msg:
                return err_msg, False
        elif product == cls.ACCELERATE:
            match_type = request.args.get('match_type', '')
            m = {
                'video': VideoMatchService,
                'voice': VoiceMatchService,
                'text': AnoyMatchService
            }
            data, status = getattr(m.get(match_type, AnoyMatchService), 'accelerate')(user_id)
            print data, status
            if not status:
                return data, False
        elif product == cls.ACCOST_RESET:
            data, status = AntiSpamService.reset_accost(user_id)
            if not status:
                return data, False
        elif product == cls.PALM_RESULT:
            data, status = PalmService.can_get_result(user_id)
            if not status:
                return data, False
        err_msg = cls.change_diamonds(user_id, -diamonds)
        if err_msg:
            return err_msg, False
        AccountFlowRecord.create(user_id, AccountFlowRecord.CONSUME, diamonds)
        return None, True

    @classmethod
    def deposit_diamonds(cls, user_id, payload):
        diamonds = payload.get('diamonds')
        if not isinstance(diamonds, int):
            return u'error request diamonds', False
        if diamonds >= 100:
            return u'authorize false, please retry', False
        err_msg = cls.change_diamonds(user_id, diamonds)
        if err_msg:
            return err_msg, False
        AccountFlowRecord.create(user_id, AccountFlowRecord.DEPOSIT, diamonds)
        return None, True

    @classmethod
    def deposit_by_activity(cls, user_id, activity):
        if activity not in cls.PAY_ACTIVITIES:
            return u'not recognized activity', False
        diamonds = cls.PAY_ACTIVITIES.get(activity)
        err_msg = cls.change_diamonds(user_id, diamonds)
        if err_msg:
            return err_msg, False
        AccountFlowRecord.create(user_id, AccountFlowRecord.ADD_BY_ACTIVITY, diamonds)
        return None, True

    @classmethod
    def get_product_info(cls, user_id=None):
        return cls.PRODUCT_INFOS, True
