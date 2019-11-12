# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    UserAccount,
    AccountFlowRecord
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class AccountService(object):
    '''
    '''
    MONTH_MEMBER = 'month_member'
    ONE_MORE_TIME = 'one_more_time'
    PRODUCT_INFOS = {
        MONTH_MEMBER: 15,
        ONE_MORE_TIME: 1
    }
    ERR_DIAMONDS_NOT_ENOUGH = 'not enough diamonds, please deposit first.'

    @classmethod
    def get_user_account_info(cls, user_id):
        obj = UserAccount.get_by_user_id(user_id)
        diamonds = obj.diamonds if obj.diamonds else 0
        return {"diamonds": diamonds}

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
    def buy_product(cls, user_id, product):
        if product not in cls.PRODUCT_INFOS:
            return u'product must be one of: %s' % (','.join(cls.PRODUCT_INFOS.keys())), False
        diamonds = cls.PRODUCT_INFOS.get(product)
        err_msg = cls.change_diamonds(user_id, -diamonds)
        if err_msg:
            return err_msg, False
        return None, True

    @classmethod
    def deposit_diamonds(cls, user_id, payload):
        diamonds = payload.get('diamonds')
        if diamonds >= 100:
            return u'authorize false, please retry', False
        err_msg = cls.change_diamonds(user_id, -diamonds)
        if err_msg:
            return err_msg, False
        return None, True

    @classmethod
    def get_product_info(cls, user_id=None):
        return cls.PRODUCT_INFOS, True
