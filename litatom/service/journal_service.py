# coding: utf-8
import json
import datetime
import time
import string
import logging
import bson
from ..model import *
from ..util import (
    get_zero_today,
    next_date,
    date_to_int_time,
    write_data_to_xls,
    ensure_path,
    now_date_key
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
    def get_objids(cls, expression):

        m = {}
        chrs = set([chr(ord('0') + el) for el in range(10)] + [chr(ord('a') + el) for el in range(26)])
        str_buff = ''
        for _ in expression:
            if _ in chrs:
                str_buff += _
                if len(str_buff) == 24:
                    if bson.ObjectId.is_valid(str_buff):
                        m[str_buff] = str_buff
            else:
                str_buff = ''
        return m

    @classmethod
    def _cal_by_others(cls, expression):
        m = cls.get_objids(expression)
        res_m = {}
        for k in m:
            res_m[k] = cls.cal_by_id(k)
        for el in res_m:
            expression = expression.replace(el, str(res_m[el]['num']))
        return eval(expression)

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
            num =  cls._cal_by_others(expression)
            return {
                "id": item_id,
                "num": num,
                "name": item.name
            }
        else:
            zeroToday = get_zero_today()
            zeroYestoday = next_date(zeroToday, -1)
            is_int = isinstance(eval(table_name + '.' + judge_field), IntField)
            if not is_int:
                time_str = "%s__gte=%r, %s__lte=%r" % (judge_field, zeroYestoday, judge_field, zeroToday)
            else:
                time_str = "%s__gte=%r, %s__lte=%r" % (judge_field, date_to_int_time(zeroYestoday), judge_field, date_to_int_time(zeroToday))
            expression = '' if not expression else expression
            exc_str = '%s.objects(%s,%s).count()' % (table_name, time_str, expression)
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

    @classmethod
    def out_port_result(cls, dst_addr):
        res_lst = []
        cnt = 0
        for item in StatItems.objects():
            m = cls.cal_by_id(str(item.id))
            name, num = m['name'], m['num']
            res_lst.append([name, num])
            cnt += 1
            if cnt >= 3:
                break
        # dst_addr = '/data/statres/%s.xlsx' % now_date_key()
        # ensure_path(dst_addr)
        write_data_to_xls(dst_addr, [u'名字', u'数量'], res_lst)