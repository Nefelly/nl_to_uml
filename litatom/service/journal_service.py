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
    IS_TESTING = True
    DATE_DIS = datetime.timedelta(hours=0)

    USER_LOC = {}   # user_id:language
    NEW_USER_LOC = {}   # 最近一天创建的用户为新用户 user_id:language
    LOC_STATED = ['TH', 'VN', 'PH'] # new_TH, count_TH
    CACHED_RES = {}
    ZERO_TODAY = None
    GENDERS = ['boy','girl']
    USER_GEN = {}   # user_id:gender

    '''
    类的预装载函数，把现有的LOC_STATED，加上new_，和count_前缀,同时准备USER_LOC,NEW_USER_LOC
    '''
    @classmethod
    def load_user_loc(cls):
        to_append = []
        for loc in cls.LOC_STATED:
            to_append.append(cls._get_new_loc(loc))
        for loc in cls.LOC_STATED:
            to_append.append(cls._get_count_loc(loc))
        cls.LOC_STATED += to_append
        if not cls.IS_TESTING:
            objs = UserSetting.objects()
        else:
            objs = UserSetting.objects().limit(1000)
        for obj in objs:
            cls.USER_LOC[obj.user_id] = obj.lang
        new_users = eval('UserSetting.objects(%s)' % cls._get_time_str('UserSetting', 'create_time'))
        for obj in new_users:
            cls.NEW_USER_LOC[obj.user_id] = obj.lang

    @classmethod
    def load_user_gen(cls):
        if not cls.IS_TESTING:
            objs = User.objects()
        else:
            objs = User.objects().limit(1000)
        for obj in objs:
            if obj.gender in cls.GENDERS:
                cls.USER_GEN[str(obj.id)] = obj.gender
        print cls.USER_GEN

    @classmethod
    def get_journal_items(cls, stat_type):
        res = []
        for el in StatItems.get_items_by_type(stat_type):
            res.append(el.to_json())
        return res, True

    @classmethod
    def _get_new_loc(cls, loc):
        return 'new_' + loc

    @classmethod
    def _get_count_loc(cls, loc):
        return 'new_count_' + loc

    '''
    输入一个StatItems Document，
    返回一个dict，返回该item的id,name,num：最近一天item对应表中的用户数量
    以及各种location,new_loc,count_loc最近一天对应表中的用户数量
    '''
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
        gender_cnts = {}
        for gender in cls.GENDERS:
            gender_cnts[gender] = 0.0
        # 遍历item对应表中的最近一天结果集的每个user_id
        for user_id in eval(exc_str):
            cnt += 1
            gender = cls.USER_GEN.get(user_id)
            print user_id,gender
            if gender in gender_cnts:
                gender_cnts[gender] += 1
            loc = cls.USER_LOC.get(user_id)
            if loc in cls.LOC_STATED:
                loc_cnts[loc] += 1
            new_loc = cls.NEW_USER_LOC.get(user_id)
            if new_loc in cls.LOC_STATED:
                loc_cnts[cls._get_new_loc(new_loc)] += 1
                loc_cnts[cls._get_count_loc(new_loc)] += 1
        res["num"] = cnt
        res.update(gender_cnts)
        res.update(loc_cnts)
        return res

    @classmethod
    def add_stat_item(cls, name, table_name, stat_type, judge_field, expression):
        if not judge_field:
            judge_field = ''
        StatItems.create(name, table_name, stat_type, judge_field, expression)
        return None, True

    '''
    无table_name的统计量中，expression的操作数即为一个统计量id,都是24位十六进制，
    get_objids()返回一个dict，每一项都是一个操作数，类型都为str
    '''
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

    '''
    expression是一个表达式，str类型，包含若干操作数和基本运算符(python eval()可以接受的运算符);
    操作数是一个24位的统计量ID，expression是基于其它统计量的一个运算；
    返回一个dict，key为'num'的为主要计算结果，基于其它统计量的'num'结果
    如果need_loc=True，会针对每个location，分别基于其它统计量的'loc'结果，进行计算，key为各种'loc'
    '''
    @classmethod
    def _cal_by_others(cls, expression, need_loc=True):
        def cal_exp(exp):
            try:
                if '/' in exp:
                    return round(eval(exp), 4)
                return eval(exp)
            except:
                return 0
        # m是一个字典，其中包含Expression各个操作数，每个操作数实际上是一个统计量
        m = cls.get_objids(expression)
        # 在res_m中，对各个统计量递归的分别计算结果
        res_m = {}
        for k in m:
            res_m[k] = cls.cal_by_id(k)
        tmp_exp = expression
        # 把表达式中各个操作数统计量的结果num写入tmp_exp，类型为str
        for el in res_m:
            tmp_exp = tmp_exp.replace(el, str(res_m[el]['num']))
        # num中存储了表达式的值
        num = cal_exp(tmp_exp)
        loc_cnts = {"num": num}
        # 将性别数量分别计算
        for gender in cls.GENDERS:
            tmp_exp = expression
            for el in res_m:
                tmp_exp=tmp_exp.replace(el,str(res_m[el][gender]))
            loc_cnts[gender] = cal_exp(tmp_exp)
        # 如果需要location信息，则对每个location的数量分别计算
        if need_loc:
            for loc in cls.LOC_STATED:
                tmp_exp = expression
                for el in res_m:
                    tmp_exp = tmp_exp.replace(el, str(res_m[el][loc]))
                loc_cnts[loc] = cal_exp(tmp_exp)
        return loc_cnts

    '''
    返回前一天的时间段，时间是从ZERO_TODAY往前倒数一天，ZERO_TODAY：1.类属性设定 2.调用时指定 3.当前时间
    table_name.judge_field为IntField或FloatField，用于判断数据库访问字符串格式
    返回的时间段限制字符串可以直接用于检索数据库
    '''
    @classmethod
    def _get_time_str(cls, table_name, judge_field, date=None):
        if date:
            zeroToday = date
        else:
            zeroToday = get_zero_today()
        if cls.ZERO_TODAY:
            zeroToday = cls.ZERO_TODAY
        # zeroToday = datetime.datetime(2019, 11, 29)
        zeroYesterday = next_date(zeroToday, -1) + cls.DATE_DIS
        is_int = isinstance(eval(table_name + '.' + judge_field), IntField)
        if not is_int:
            time_str = "%s__gte=%r, %s__lte=%r" % (judge_field, zeroYesterday, judge_field, zeroToday)
        else:
            time_str = "%s__gte=%r, %s__lte=%r" % (
            judge_field, date_to_int_time(zeroYesterday), judge_field, date_to_int_time(zeroToday))
        return time_str

    '''
    通过统计量对应的id,返回一个dict，有id,name,num,loc,new_loc,count_loc各个字段，
    对满足item条件限制的对象不做去重
    '''
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

        # 根据输入的item_id,获得StatItems类的Document，即为一个统计量
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
        # 如果该统计量是复合的，没有相应的表存储信息，则根据其表达式expression计算结果
        # id,name,num,以及各种loc，为返回结果res，类型为一个dict
        if not table_name:
            loc_cnts = cls._cal_by_others(expression, need_loc)
            res = {
                "id": item_id,
                "name": item.name
            }
            res.update(loc_cnts)
        # 如果该统计量需要的信息都在某一表内，其表达式expression与上一种情况格式不同，可有可无；
        # 有expression时，其包含若干字段，每一个字段作为一个检索数据库的限制条件
        # id,name,num为返回结果res，类型为一个dict
        # 如果need_loc，则res中增加各种loc,new_loc,count_loc字段
        else:
            time_str = cls._get_time_str(table_name, judge_field)
            expression = '' if not expression else expression
            if not cls.IS_TESTING:
                exc_str = '%s.objects(%s,%s).count()' % (table_name, time_str, expression)
            else:
                exc_str = '%s.objects(%s,%s).limit(1000).count()' % (table_name, time_str, expression)
            print exc_str
            # cnt表示一天时间内，满足该统计量限制的记录个数
            cnt = eval(exc_str)
            if not cnt:
                cnt = 0
            gender_cnts={}
            for gender in cls.GENDERS:
                gender_cnts[gender]=0.0
            loc_cnts = {}
            table_user_id = {
                "Report": "target_uid",
                "Feedback": "uid"
            }
            # 对每个location，在loc_cnts这个dict中，存三个字段，loc,new_loc,count_loc
            if need_loc:
                for loc in cls.LOC_STATED:
                    loc_cnts[loc] = 0
                    loc_cnts[cls._get_new_loc(loc)] = 0.0
                    loc_cnts[cls._get_count_loc(loc)] = 0.0
                # 只对有count且不大于1000000的才进行分location统计
                if cnt and cnt < 1000000:
                    eval_str = '%s.objects(%s,%s)' % (table_name, time_str, expression)
                    if cls.IS_TESTING:
                        eval_str += '.limit(1000)'
                    new_user_acted = {}
                    # 遍历满足统计量限制的结果集
                    for obj in eval(eval_str):
                        if table_name == 'User':
                            user_id = str(obj.id)
                        elif table_name in table_user_id:
                            user_id = getattr(obj, table_user_id[table_name])
                            # user_id = str(obj.target_uid)
                        else:
                            user_id = obj.user_id
                        gender=cls.USER_GEN.get(user_id)
                        if gender in gender_cnts:
                            gender_cnts[gender] += 1
                        loc = cls.USER_LOC.get(user_id)
                        if loc and loc in loc_cnts:
                            loc_cnts[loc] += 1
                        new_loc = cls.NEW_USER_LOC.get(user_id)
                        if new_loc in cls.LOC_STATED:
                            loc_cnts[cls._get_new_loc(new_loc)] += 1
                            if not new_user_acted.get(user_id):
                                loc_cnts[cls._get_count_loc(new_loc)] += 1
                                new_user_acted[user_id] = 1
            else:
                eval_str = '%s.objects(%s,%s)' % (table_name, time_str, expression)
                for obj in eval(eval_str):
                    if table_name == 'User':
                        user_id = str(obj.id)
                    elif table_name in table_user_id:
                        user_id = getattr(obj, table_user_id[table_name])
                    else:
                        user_id = obj.user_id
                    gender=cls.USER_GEN.get(user_id)
                    if gender in gender_cnts:
                        gender_cnts[gender] += 1
            res = {
                "id": item_id,
                "num": cnt,
                "name": item.name
            }
            res.update(loc_cnts)
            res.update(gender_cnts)
        cls.CACHED_RES[item_id] = res
        return res

    @classmethod
    def delete_stat_item(cls, item_id):
        StatItems.objects(id=item_id).delete()
        return None, True

    @classmethod
    def out_port_result(cls, dst_addr):
        cls.load_user_loc()
        print 'load succ', cls.LOC_STATED
        cls.load_user_gen()
        res_lst = []
        cls.DATE_DIS = datetime.timedelta(hours=0)
        cnt = 0
        # daily_m是一个dict类型变量,id,name为抽样日活，num为最近一日日活用户数量，以及各种loc中的各种日活用户数量
        daily_m = cls.daily_active(StatItems.objects(name=u'抽样日活').first())
        print 'load daily_m'
        # 遍历StatItems中所有类型为BUSINESS_TYPE的统计量item
        for item in StatItems.get_items_by_type(StatItems.BUSINESS_TYPE):
            try:
                # m为根据该统计量的id计算得到的结果
                m = cls.cal_by_id(str(item.id))
                name, num = m['name'], m['num']
                gender_cnt = [m[gender] for gender in cls.GENDERS]
                print gender_cnt
                region_cnt = [m[loc] for loc in cls.LOC_STATED]
                avr_cnt = []
                for loc in cls.LOC_STATED:
                    if daily_m[loc]:
                        avr_cnt.append(round(m.get(loc, 0)/daily_m[loc], 4))
                    else:
                        avr_cnt.append(0)
                res_lst.append([name, num] + gender_cnt + region_cnt + [num/daily_m['num']] + avr_cnt)
                cnt += 1
            except Exception, e:
                print e
                continue
            # if cnt >= 3:
            #     break
        # dst_addr = '/data/statres/%s.xlsx' % now_date_key()
        # ensure_path(dst_addr)
        # print res_lst
        write_data_to_xls(dst_addr, [u'名字', u'数量'] + cls.GENDERS + cls.LOC_STATED + ['total avr'] + [el + 'avr' for el in cls.LOC_STATED], res_lst)

    @classmethod
    def ad_res(cls, dst_addr):
        # cls.load_user_loc()
        res_lst = []
        cnt = 0
        daily_m = cls.daily_active(StatItems.objects(name=u'抽样日活').first())
        cls.DATE_DIS = datetime.timedelta(hours=-16)
        for item in StatItems.get_items_by_type(StatItems.AD_TYPE):
            try:
                m = cls.cal_by_id(str(item.id))
                name, num = m['name'], m['num']
                region_cnt = [m[loc] for loc in cls.LOC_STATED]
                avr_cnt = []
                for loc in cls.LOC_STATED:
                    if daily_m[loc]:
                        avr_cnt.append(round(m.get(loc, 0) / daily_m[loc], 4))
                    else:
                        avr_cnt.append(0)
                res_lst.append([name, num] + region_cnt + [num / daily_m['num']] + avr_cnt)
                cnt += 1
            except Exception, e:
                print e
                continue
            # if cnt >= 3:
            #     break
        # dst_addr = '/data/statres/%s.xlsx' % now_date_key()
        # ensure_path(dst_addr)
        # print res_lst
        write_data_to_xls(dst_addr,
                          [u'名字', u'数量'] + cls.LOC_STATED + ['total avr'] + [el + 'avr' for el in cls.LOC_STATED],
                          res_lst)
        return
