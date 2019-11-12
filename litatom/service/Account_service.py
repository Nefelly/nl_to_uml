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
    @classmethod
    def get_user_account_info(cls, user_id):
        obj = UserAccount.get_by_user_id(user_id)
        diamonds = obj.diamonds if obj.diamonds else 0
        return {"diamonds": diamonds}

    @classmethod
    def buy_product(cls, user_id, product):
        return

    @classmethod
    def deposit_diamonds(cls, user_id, payload):
        return
