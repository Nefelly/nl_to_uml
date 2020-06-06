# coding: utf-8
import json
import time
import traceback
from ..model import (
    Gift,
    ReceivedGift
)
from ..service import (
    UserService
)
import logging
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class GiftService(object):
    '''
    '''

    @classmethod
    def get_gifts(cls):
        return Gift.get_gifts(), True

    @classmethod
    def gift_price_by_gift_id(cls, gift_id):
        gifts = Gift.gift_price_m()
        return gifts.get(gift_id, 0)

    @classmethod
    def received_gifts(cls, user_id, page_num, num):
        objs = ReceivedGift.get_by_receiver_id(user_id, page_num, num)
        # is_member = AccountService.is_member(user_id)
        res = []
        for obj in objs:
            res.append(obj.to_json())
        user_ids = [el.user_id for el in objs]
        user_info_m = UserService.batch_get_user_info_m(user_ids)
        for i in range(len(res)):
            user_id = res[i]['user_id']
            res[i]['user_info'] = user_info_m.get(user_id, {})
        return {'gifts': res}, True

    @classmethod
    def send_gift(cls, user_id, receiver_id, gift_id):
        ReceivedGift.create(user_id, receiver_id, gift_id)
        return None, True
