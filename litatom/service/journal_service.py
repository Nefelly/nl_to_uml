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
    IS_TESTING = False

    USER_LOC = {}
    LOC_STATED = ['TH', 'VN']
    CACHED_RES = {}

    @classmethod
    def load_user_loc(cls):
        if not cls.IS_TESTING:
            objs = UserSetting.objects()
        else:
            objs = UserSetting.objects().limit(1000)
        for obj in objs:
            cls.USER_LOC[obj.user_id] = obj.lang

    @classmethod
    def get_journal_items(cls):
        res = []
        for el in StatItems.objects():
            res.append(el.to_json())
        return res, True

    @classmethod
    def daily_active(cls, item, date=None):
        res = {
            "id": str(item.id),
            "name": item.name
        }
        table_name = item.table_name
        judge_field = item.judge_field
        time_str = cls._get_time_str(table_name, judge_field)
        exc_str = '%s.objects(%s).distinct("user_id")' % (table_name, time_str)
        cnt = 0.0
        loc_cnts = {}
        for loc in cls.LOC_STATED:
            loc_cnts[loc] = 0.0
        for user_id in eval(exc_str):
            cnt += 1
            loc = cls.USER_LOC.get(user_id)
            if loc in cls.LOC_STATED:
                loc_cnts[loc] += 1
        res["num"] = cnt
        res.update(loc_cnts)
        return res

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
    def _cal_by_others(cls, expression, need_loc=True):
        def cal_exp(exp):
            try:
                return eval(exp)
            except:
                return 0
        m = cls.get_objids(expression)
        res_m = {}
        for k in m:
            res_m[k] = cls.cal_by_id(k)
        tmp_exp = expression
        for el in res_m:
            tmp_exp = tmp_exp.replace(el, str(res_m[el]['num']))
        num = cal_exp(tmp_exp)
        loc_cnts = {"num": num}
        if need_loc:
            for loc in cls.LOC_STATED:
                tmp_exp = expression
                for el in res_m:
                    tmp_exp = tmp_exp.replace(el, str(res_m[el][loc]))
                loc_cnts[loc] = cal_exp(tmp_exp)
        return loc_cnts

    @classmethod
    def _get_time_str(cls, table_name, judge_field, date=None):
        if date:
            zeroToday = date
        else:
            zeroToday = get_zero_today()
        # zeroToday = datetime.datetime(2019, 11, 16)
        zeroYestoday = next_date(zeroToday, -1)
        is_int = isinstance(eval(table_name + '.' + judge_field), IntField)
        if not is_int:
            time_str = "%s__gte=%r, %s__lte=%r" % (judge_field, zeroYestoday, judge_field, zeroToday)
        else:
            time_str = "%s__gte=%r, %s__lte=%r" % (
            judge_field, date_to_int_time(zeroYestoday), judge_field, date_to_int_time(zeroToday))
        return time_str

    @classmethod
    def cal_by_id(cls, item_id, need_loc=True):
        def check_valid_string(word):
            chars = string.ascii_letters + '_' + string.digits
            for chr in word:
                if chr not in chars:
                    return False
            return True
        if cls.CACHED_RES.get(item_id):
            return cls.CACHED_RES[item_id]

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
        name_func = {
            u'抽样日活': cls.daily_active
        }
        if item.name in name_func:
            return name_func[item.name](item)
        item_id = str(item.id)
        table_name = item.table_name
        judge_field = item.judge_field
        expression = item.expression
        if not item.table_name:
            loc_cnts = cls._cal_by_others(expression, need_loc)
            res = {
                "id": item_id,
                "name": item.name
            }
            res.update(loc_cnts)
        else:
            time_str = cls._get_time_str(table_name, judge_field)
            expression = '' if not expression else expression
            if not cls.IS_TESTING:
                exc_str = '%s.objects(%s,%s).count()' % (table_name, time_str, expression)
            else:
                exc_str = '%s.objects(%s,%s).limit(1000).count()' % (table_name, time_str, expression)
            print exc_str
            cnt = eval(exc_str)
            if not cnt:
                cnt = 0
            loc_cnts = {}
            table_user_id = {
                "Report": "target_uid",
                "Feedback": "uid"
            }
            if need_loc:
                for loc in cls.LOC_STATED:
                    loc_cnts[loc] = 0
                if cnt and cnt < 1000000:
                    eval_str = '%s.objects(%s,%s)' % (table_name, time_str, expression)
                    if cls.IS_TESTING:
                        eval_str += '.limit(1000)'
                    for obj in eval(eval_str):
                        if table_name == 'User':
                            user_id = str(obj.id)
                        elif table_name in table_user_id:
                            user_id = getattr(obj, table_user_id[table_name])
                            # user_id = str(obj.target_uid)
                        else:
                            user_id = obj.user_id
                        loc = cls.USER_LOC.get(user_id)
                        if loc and loc in loc_cnts:
                            loc_cnts[loc] += 1
            res = {
                "id": item_id,
                "num": cnt,
                "name": item.name
            }
            res.update(loc_cnts)
        cls.CACHED_RES[item_id] = res
        return res

    @classmethod
    def delete_stat_item(cls, item_id):
        StatItems.objects(id=item_id).delete()
        return None, True

    @classmethod
    def out_port_result(cls, dst_addr):
        cls.load_user_loc()
        res_lst = []
        cnt = 0
        daily_m = cls.daily_active(StatItems.objects(name=u'抽样日活').first())
        for item in StatItems.objects():
            try:
                m = cls.cal_by_id(str(item.id))
                name, num = m['name'], m['num']
                region_cnt = [m[loc] for loc in cls.LOC_STATED]
                avr_cnt = []
                for loc in cls.LOC_STATED:
                    if daily_m[loc]:
                        avr_cnt.append(m.get(loc, 0)/daily_m[loc])
                    else:
                        avr_cnt.append(0)
                res_lst.append([name, num] + region_cnt + [num/daily_m['num']] + avr_cnt)
                cnt += 1
            except Exception, e:
                print e
                continue
            # if cnt >= 3:
            #     break
        # dst_addr = '/data/statres/%s.xlsx' % now_date_key()
        # ensure_path(dst_addr)
        # print res_lst
        write_data_to_xls(dst_addr, [u'名字', u'数量'] + cls.LOC_STATED + ['total avr'] + [el + 'avr' for el in cls.LOC_STATED], res_lst)

    @classmethod
    def ad_res(cls):
        return
