# coding: utf-8
import json
import time
import traceback
from ..model import (
    Tag,
    UserTag
)
from ..service import (
    UserService,
    GlobalizationService
)
import logging
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class UserTagService(object):
    '''
    '''

    @classmethod
    def get_real_name(cls, name):
        region_tag = name.replace(' ', '_')
        return GlobalizationService.get_cached_region_word(region_tag)

    @classmethod
    def get_tags(cls):
        raw_gifts = Tag.get_tags()
        res = []
        for i in range(len(raw_gifts)):
            raw_gifts[i]['name'] = cls.get_real_name(raw_gifts[i]['name'])
        return raw_gifts, True

    @classmethod
    def add_tags(cls, user_id, tag_ids):
        return None, True

    @classmethod
    def gift_price_by_gift_id(cls, gift_id):
        gifts = Gift.gift_price_m()
        return gifts.get(gift_id, 0)

    @classmethod
    def get_gift_id_giftnames_m(cls):
        res = {}
        raw_gifts, status = cls.get_gifts()
        for el in raw_gifts:
            res[el['id']] = el['name']
        return res

    @classmethod
    def received_gifts(cls, user_id, page_num, num):
        objs = ReceivedGift.get_by_receiver_id(user_id, page_num, num)
        # is_member = AccountService.is_member(user_id)
        gift_names = cls.get_gift_id_giftnames_m()
        res = []
        for obj in objs:
            tmp = obj.to_json()
            tmp['gift_name'] = gift_names.get(obj.gift_id)
            res.append(tmp)
        user_ids = [el.sender for el in objs]
        user_info_m = UserService.batch_get_user_info_m(user_ids)
        for i in range(len(res)):
            user_id = res[i]['sender']
            res[i]['user_info'] = user_info_m.get(user_id, {})
        return {'gifts': res}, True

    @classmethod
    def send_gift(cls, user_id, receiver_id, gift_id):
        ReceivedGift.create(user_id, receiver_id, gift_id)
        return None
