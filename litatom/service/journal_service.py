# coding: utf-8
import json
import time
import traceback
import logging
from ..model import *
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class JournalService(object):
    '''
    '''

    @classmethod
    def get_journal_items(cls):
        res = []
        for el in StatItems.objects():
            res.append(el.to_json())
        return res, True

    @classmethod
    def add_stat_item(cls, name, table_name, judge_field, expression):
        if not judge_field:
            judge_field = ''
        StatItems.create(name, table_name, judge_field, expression)
        return None, True

    @classmethod
    def cal_by_id(cls, item_id):
        item = StatItems.get_by_id(item_id)
        return {
            "id": item_id,
            "num": 0,
            "name": item.name
        }
    @classmethod
    def delete_stat_item(cls, item_id):
        StatItems.objects(id=item_id).delete()
        return None, True
