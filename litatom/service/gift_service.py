# coding: utf-8
import json
import time
import traceback
from ..model import (
    Gift,
    ReceivedGift
)
from ..service import (
    UserService,
    GlobalizationService
)
import logging
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class GiftService(object):
    '''
    '''

    @classmethod
    def get_tag(cls, name):
        return 'gift' + '_' + name.replace(' ', '_')

    @classmethod
    def get_gifts(cls):
        raw_gifts = Gift.get_gifts()
        for i in range(len(raw_gifts)):
            tag = cls.get_tag(raw_gifts[i]['name'])
            raw_gifts[i]['name'] = GlobalizationService.get_cached_region_word(tag)
        return raw_gifts, True

    @classmethod
    def gift_price_by_gift_id(cls, gift_id):
        gifts = Gift.gift_price_m()
        return gifts.get(gift_id, 0)

    @classmethod
    def get_gift_id_infos_m(cls):
        res = {}
        raw_gifts, status = cls.get_gifts()
        for el in raw_gifts:
            res[el['id']] = {
                'name': el['name'],
                'file_id': el['fileid'],
                'thumbnail': el['thumbnail']
                }
        return res

    @classmethod
    def received_gifts(cls, user_id, page_num, num):
        objs = ReceivedGift.get_by_receiver_id(user_id, page_num, num)
        gift_infos = cls.get_gift_id_infos_m()
        res = []
        for obj in objs:
            tmp = obj.to_json()
            tmp.update(gift_infos.get(obj.gift_id, {}))
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

    @classmethod
    def add_region_word(cls):
        from ..model import RegionWord
        for el in Gift.objects():
            tag = cls.get_tag(el.name)
            RegionWord.add_or_mod(RegionWord.REGION_BENCHMARK, tag, el.name)

    @classmethod
    def add_region_word(cls, obj):
        from ..model import RegionWord
        RegionWord.add_or_mod(RegionWord.REGION_BENCHMARK,  cls.get_tag(obj.name), obj.name)
