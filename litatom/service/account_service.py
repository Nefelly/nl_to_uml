# coding: utf-8
import json
import time
import traceback
from hendrix.conf import setting
import logging
from ..model import (
    UserAccount,
    AccountFlowRecord
)
from ..const import (
    ONE_WEEK,
    ONE_MIN,
    ONE_DAY
)
from ..util import (
    now_date_key
)
from ..service import (
    MatchService,
    AnoyMatchService,
    VoiceMatchService,
    VideoMatchService,
    AccostService,
    PalmService,
    UserService,
    AdService,
    AliLogService
)
from ..key import (
    REDIS_ACCOUNT_ACTION,
    REDIS_DEPOSIT_BY_ACTIVITY,
    REDIS_SHARE_LIMIT
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
        WEEK_MEMBER: 20 if not setting.IS_DEV else 1,
        ONE_MORE_TIME: 1,
        ACCELERATE: 1,
        ACCOST_RESET: 1,
        PALM_RESULT: 10
    }
    SHARE = 'share'
    WATCH_AD = 'watch_video'
    SHARE_5 = 'share_5'     # 链接分享，被5个人点开
    PAY_ACTIVITIES = {
        SHARE: 10,
        WATCH_AD: 1,
        SHARE_5: 100,
    }
    UNBAN_DIAMONDS = 1000
    DAY_ACTIVITY_LIMIT = 500 if not setting.IS_DEV else 200
    MEMBER_SHIPS = [WEEK_MEMBER]
    ERR_DIAMONDS_NOT_ENOUGH = 'not enough diamonds, please deposit first.'

    @classmethod
    def diamond_products(cls):
        return {
            '500diamonds': 500,
            '200diamonds': 200,
            '100_diamonds': 100,
            '10diamonds': 50,
            # 'asfd324': 5,
            # '324asd': 15
        }, True

    @classmethod
    def get_product_name_by_diamonds(cls, diamonds):
        product_set, res = cls.diamond_products()
        for product in product_set:
            if product_set[product] == diamonds:
                return product
        return None

    @classmethod
    def get_user_account_info(cls, user_id):
        return UserAccount.get_account_info(user_id)

    @classmethod
    def unban_by_diamonds(cls, user_id):
        if UserService.device_blocked():
            return UserService.ERROR_DEVICE_FORBIDDEN, False
        if not UserService.is_forbbiden(user_id):
            ''' 不用重新登陆'''
            # from ..model import User
            # user = User.get_by_id(user_id)
            # UserService._trans_forbidden_2_session(user)

            UserService.clear_forbidden_session(request.session_id.replace('session.', ''))
            return u'you are not forbbiden', False
        msg = cls.change_diamonds(user_id, -cls.UNBAN_DIAMONDS, 'unban_by_diamonds')
        if not msg:
            if UserService.unban_user(user_id):
                 return None, True
        return msg, False

    @classmethod
    def record_to_ali(cls, user_id, name, diamonds):
        content = [('user_id', user_id), ('name', name), ('diamonds', str(diamonds)), ('loc', request.loc)]
        AliLogService.put_logs(content, '', '', 'litatom-account', 'account_flow')

    @classmethod
    def change_diamonds(cls, user_id, diamonds, name='unknown'):
        user_account = UserAccount.get_by_user_id(user_id)
        if not user_account:
            user_account = UserAccount.create_account(user_id)
        if diamonds >= 0:
            user_account.diamonds += diamonds
            user_account.save()
            cls.record_to_ali(user_id, name, diamonds)
            return None
        else:
            if user_account.diamonds + diamonds >= 0:
                user_account.diamonds += diamonds
                user_account.save()
                cls.record_to_ali(user_id, name, diamonds)
                return None
            return cls.ERR_DIAMONDS_NOT_ENOUGH

    @classmethod
    def set_diamonds(cls, user_id, num):
        user_account = UserAccount.get_by_user_id(user_id)
        if not user_account:
            user_account = UserAccount.create_account(user_id)
        user_account.diamonds = num
        user_account.save()
        return None, True

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
            time_int = ONE_WEEK if not setting.IS_DEV else ONE_MIN
            user_account.membership_time = old_membership_time + time_int
            user_account.save()
        MatchService.set_member_match_left(user_id)
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
            if not status:
                return data, False
        elif product == cls.ACCOST_RESET:
            data, status = AccostService.reset_accost(user_id)
            if not status:
                return data, False
        elif product == cls.PALM_RESULT:
            data, status = PalmService.can_get_result(user_id)
            if not status:
                return data, False
        err_msg = cls.change_diamonds(user_id, -diamonds, product)
        if err_msg:
            return err_msg, False
        AccountFlowRecord.create(user_id, AccountFlowRecord.CONSUME, diamonds)
        return None, True

    @classmethod
    def deposit_diamonds(cls, user_id, payload):
        token = payload.get('payload', {}).get('token')
        diamonds = payload.get('diamonds')
        if not token:
            AccountFlowRecord.create(user_id, AccountFlowRecord.WRONG, diamonds)
        else:
            key = REDIS_ACCOUNT_ACTION.format(key=('pay' + token))
            r = redis_client.get(key)
            if r:
                return 'Already deposit success', False
            redis_client.setex(key, ONE_WEEK, 1)
        if not isinstance(diamonds, int):
            return u'error request diamonds', False
        # if diamonds >= 10000:
        #     return u'authorize false, please retry', False
        err_msg = cls.change_diamonds(user_id, diamonds, 'deposit')
        if err_msg:
            return err_msg, False
        AccountFlowRecord.create(user_id, AccountFlowRecord.DEPOSIT, diamonds)
        return None, True

    @classmethod
    def deposit_by_activity(cls, user_id, activity, other_info={}):
        if activity not in cls.PAY_ACTIVITIES:
            return u'not recognized activity', False
        diamonds = cls.PAY_ACTIVITIES.get(activity)
        key = REDIS_DEPOSIT_BY_ACTIVITY.format(user_date=now_date_key() + user_id)
        day_deposit_str = redis_client.get(key)
        day_deposit = int(day_deposit_str) if day_deposit_str else 0
        new_day_deposit = day_deposit + diamonds
        if new_day_deposit > cls.DAY_ACTIVITY_LIMIT:
            return u'you have deposit by activity too much today, please try again tomorrow', False
        if activity == cls.SHARE:
            key = REDIS_SHARE_LIMIT.format(user_id=user_id)
            if redis_client.get(key):
                return u'you have been shared', False
            redis_client.set(key, True, ONE_WEEK)
        redis_client.set(key, new_day_deposit, ONE_DAY)
        if activity == cls.WATCH_AD:
            data, status = AdService.verify_ad_viewed(user_id, other_info)
            if not status:
                return data, status
        err_msg = cls.change_diamonds(user_id, diamonds, activity)
        if err_msg:
            return err_msg, False
        AccountFlowRecord.create(user_id, AccountFlowRecord.ADD_BY_ACTIVITY, diamonds)
        return None, True

    @classmethod
    def get_product_info(cls, user_id=None):
        return cls.PRODUCT_INFOS, True

    @classmethod
    def get_pay_activities(cls):
        return cls.PAY_ACTIVITIES, True
