# coding: utf-8
import json
import datetime
import time
import string
import logging
from ..model import *
from ..util import (
    get_zero_today,
    next_date,
    date_to_int_time
)
from mongoengine import (
    DateTimeField,
    IntField,

)

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
    def _cal_by_others(cls, expression):
        return 0.0

    @classmethod
    def cal_by_id(cls, item_id):
        def check_valid_string(word):
            chars = string.ascii_letters + '_' + string.digits
            for chr in word:
                if chr not in chars:
                    return False
            return True
        # NOT_ALLOWED = ["User", "Feed"]
        # table_name = table_name.strip()
        # fields = fields.strip().split("|")
        # main_key = main_key if main_key else ''
        # main_key = main_key.strip()
        # for el in fields + [table_name, main_key]:
        #     if not check_valid_string(el):
        #         return u'word: %s is invalid' % el, False
        # insert_data = insert_data.strip()
        # if table_name in NOT_ALLOWED:
        #     return u'Insert into table:%s is not allowed' % table_name, False
        # lines = [el.split("\t") for el in insert_data.split("\n") if el]
        # for line in lines:
        #     if len(line) != len(fields):
        #         return u'len(line) != len(fields), line:%r' % line, False
        #     conn = ','.join(['%s=\'%s\'' % (fields[i], line[i]) for i in range(len(line))])
        #     get = eval('%s.objects(%s).first()' % (table_name, conn))
        #     if not get:
        #         eval('%s(%s).save()' % (table_name, conn))

        item = StatItems.get_by_id(item_id)
        if not item:
            return {}
        item_id = str(item.id)
        table_name = item.table_name
        judge_field = item.judge_field
        expression = item.expression
        if not item.table_name:
            return cls._cal_by_others(expression)
        zeroToday = get_zero_today()
        zeroYestoday = next_date(zeroToday, -1)
        is_int = isinstance(eval(table_name + '.' + judge_field), IntField)
        if not is_int:
            time_str = "%s__gte=%r, %s__lte=%r" % (judge_field, zeroYestoday, judge_field, zeroToday)
        else:
            time_str = "%s__gte=%r, %s__lte=%r" % (judge_field, date_to_int_time(zeroYestoday), judge_field, date_to_int_time(zeroToday))
        exc_str = '%s.objects(%s,%s).count()' % (time_str, expression)
        print exc_str
        cnt = eval(exc_str)
        if not cnt:
            cnt = 0
        return {
            "id": item_id,
            "num": cnt,
            "name": item.name
        }

    @classmethod
    def delete_stat_item(cls, item_id):
        StatItems.objects(id=item_id).delete()
        return None, True
