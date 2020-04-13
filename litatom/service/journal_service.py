# coding: utf-8
import datetime
import logging
import bson
from ..model import *
from ..util import (
    get_zero_today,
    next_date,
    date_to_int_time,
    write_data_to_multisheets,
)
from mongoengine import (
    IntField,
)
from ..service import (
    AliLogService
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']


class JournalService(object):
    IS_TESTING = False
    DATE_DIS = datetime.timedelta(hours=0)

    USER_LOC = {}  # user_id:loc
    NEW_USER_LOC = {}  # 最近一天创建的用户为新用户 user_id:language
    LOC_STATED = ['TH', 'VN', 'ID']  # new_TH, count_TH
    CACHED_RES = {}
    ZERO_TODAY = None
    GENDERS = ['boy', 'girl']
    USER_GEN = {}  # user_id:gender
    ALI_LOG_STORE = ['UserAction']  # 存在ali_log_service的部分表
    CACHED_ALI_LOG = None  # 迭代器类型

    @classmethod
    def load_user_loc(cls):
        """类的预装载函数，把现有的LOC_STATED，加上new_，和count_前缀,同时准备USER_LOC,NEW_USER_LOC"""
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
        """预装载函数，将用户性别信息写入USER_GEN"""
        if not cls.IS_TESTING:
            objs = User.objects()
        else:
            objs = User.objects().limit(1000)
        for obj in objs:
            if obj.gender in cls.GENDERS:
                cls.USER_GEN[str(obj.id)] = obj.gender

    @classmethod
    def load_ali_log(cls, date):
        """预装载函数，返回一个迭代器"""
        from_time, to_time = cls._get_alilog_time_str(date)
        cls.CACHED_ALI_LOG = AliLogService.get_all_log_by_time_and_topic(from_time=from_time, to_time=to_time)

    @classmethod
    def get_journal_items(cls, stat_type):
        res = []
        for el in StatItems.get_items_by_type(stat_type):
            res.append(el.to_json())
        return res, True

    @classmethod
    def _get_res_from_query(cls, from_time, to_time, query):
        resp = AliLogService.get_log_atom(from_time=from_time, to_time=to_time, query=query)
        for log in resp.logs:
            res = log.get_contents()['res']
        return int(res)

    @classmethod
    def daily_active(cls, item, date=None):
        """
        专门计算抽样日活统计量的函数
        :param item: StatItems Document(daily_active)
        :param date:
        :return: 返回一个dict，返回daily_active的id,name,num：最近一天UserAction中的用户数量,以及
        各种location,new_loc,count_loc最近一天的用户数量
        """
        # 统计准备工作
        res = [{} for i in range(len(cls.LOC_STATED) + 1)]
        for i in res:
            i["id"] = str(item.id)
            i['name'] = item.name
            i['计数'] = 0.0
            i['boy'] = 0.0
            i['girl'] = 0.0
            i['新用户人次'] = 0.0
            i['新用户人数'] = 0.0
        from_time, to_time = cls._get_alilog_time_str(date)
        resp = AliLogService.get_log_atom(from_time=from_time, to_time=to_time,
                                          query='*|select count(distinct user_id) as res')
        logs = resp.logs
        for log in logs:
            res[0]['计数'] = int(log.get_contents()['res'])
        resp_set = AliLogService.get_log_by_time_and_topic(from_time=from_time, to_time=to_time,
                                                           query='*|select distinct user_id limit 1000000')
        uids = set()
        new_user_acted = set()
        for resp in resp_set:
            for log in resp.logs:
                user_id = log.get_contents()['user_id']
                if user_id in uids:
                    continue
                uids.add(user_id)
                cls.cal_res_by_uid(user_id, res, new_user_acted)
        return res

    @classmethod
    def add_stat_item(cls, name, table_name, stat_type, judge_field, expression):
        if not judge_field:
            judge_field = ''
        StatItems.create(name, table_name, stat_type, judge_field, expression)
        return None, True

    @classmethod
    def get_objids(cls, expression):
        """
        无table_name的统计量中，expression的操作数即为一个统计量id,都是24位十六进制，
        :param expression: 表达式
        :return: 一个dict，每一项都是一个操作数，类型都为str
        """
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
    def _cal_by_others(cls, expression, res):
        """
        :param expression: 一个表达式，str类型，包含若干操作数和基本运算符(python eval()可以接受的运算符);
        操作数是一个24位的统计量ID，expression是基于其它统计量的一个运算；
        :return: 一个dict，key为'num'的为主要计算结果，基于其它统计量的'num'结果
        """

        def cal_exp(exp):
            try:
                if '/' in exp:
                    return round(eval(exp), 4)
                return eval(exp)
            except:
                return 0

        # stat_set是一个字典，其中包含Expression各个操作数，每个操作数实际上是一个统计量
        stat_set = cls.get_objids(expression)
        # 在res_stat_set中，对各个统计量递归的分别计算结果
        res_stat_set = {}
        for stat_item in stat_set:
            res_stat_set[stat_item] = cls.cal_by_id(stat_item)

        for loc_index in range(len(res)):
            for item in res[loc_index]:
                # item 即计数,boy,girl,新用户等
                if item in ('name', 'id'):
                    continue
                tmp_exp = expression
                for stat_item in res_stat_set:
                    # print(loc_index, item, str(res_stat_set[stat_item][loc_index][item]))
                    # stat_item是表达式中的各种统计量, res_stat_set[stat_item]是一个字典，表示那一个统计量的结果
                    tmp_exp = tmp_exp.replace(stat_item, str(res_stat_set[stat_item][loc_index][item]))
                res[loc_index][item] = cal_exp(tmp_exp)
        return res

    @classmethod
    def _get_time_str(cls, table_name, judge_field, date=None):
        """
        返回前一天的时间段，时间是从ZERO_TODAY往前倒数一天，ZERO_TODAY：1.类属性设定 2.调用时指定 3.当前时间
        :param table_name:
        :param judge_field:table_name.judge_field为IntField或FloatField，用于判断数据库访问字符串格式
        :param date:
        :return:返回时间段限制字符串可以直接用于检索数据库
        """
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

    @classmethod
    def _get_alilog_time_str(cls, date=None):
        """
        返回满足阿里云日志服务的
        :param date:
        :return:返回一个tuple，前一项表示from_time，后一项表示to_time
        """
        if date:
            zeroToday = date
        else:
            zeroToday = get_zero_today()
        if cls.ZERO_TODAY:
            zeroToday = cls.ZERO_TODAY
        zeroYesterday = next_date(zeroToday, -1) + cls.DATE_DIS
        from_time = zeroYesterday.strftime("%Y-%m-%d %H:%M:%S+8:00")
        to_time = zeroToday.strftime("%Y-%m-%d %H:%M:%S+8:00")
        return from_time, to_time

    @classmethod
    def _get_stat_date(cls, date):
        """
        :param date: datetime类型
        :return: datetime类型，为输入日期的前一天
        """
        if date:
            return (date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            return (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    @classmethod
    def cal_res_by_uid(cls, user_id, res, new_user_acted):
        """根据user_id，记录入res"""
        gender = cls.USER_GEN.get(str(user_id))
        if gender and gender in cls.GENDERS:
            res[0][gender] += 1

        loc = cls.USER_LOC.get(user_id)
        if not loc or loc not in cls.LOC_STATED:
            return
        sheet_index = cls.LOC_STATED.index(loc) + 1
        res[sheet_index]['计数'] += 1
        if gender and gender in cls.GENDERS:
            res[sheet_index][gender] += 1

        new_loc = cls.NEW_USER_LOC.get(user_id)
        if new_loc not in cls.LOC_STATED:
            return
        res[0]['新用户人次'] += 1
        sheet_index = cls.LOC_STATED.index(new_loc) + 1
        res[sheet_index]['新用户人次'] += 1

        if user_id in new_user_acted:
            return
        res[0]['新用户人数'] += 1
        res[sheet_index]['新用户人数'] += 1
        new_user_acted.add(user_id)

    @classmethod
    def cal_by_id(cls, item_id):
        """
        对满足item条件限制的对象不做去重
        :param item_id: 一个统计量对应的id
        :return: 返回一个list，包含总计res和各个地区的res
        """
        if cls.CACHED_RES.get(item_id):
            return cls.CACHED_RES[item_id]

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

        # 统计准备工作
        res = [{} for i in range(len(cls.LOC_STATED) + 1)]
        for i in res:
            i["id"] = item_id
            i['name'] = item.name
            i['计数'] = 0.0
            i['boy'] = 0.0
            i['girl'] = 0.0
            i['新用户人次'] = 0.0
            i['新用户人数'] = 0.0
        # 如果该统计量是复合的，没有相应的表存储信息，则根据其表达式expression计算结果
        # id,name,num,以及各种loc，为返回结果res，类型为一个dict
        if not table_name:
            res = cls._cal_by_others(expression, res)
        # 如果该统计量需要的信息都在某一表内，且该表在阿里云上，其表达式expression与上一种情况格式不同，可有可无；
        # 有expression时，其包含若干字段，每一个字段作为一个检索数据库的限制条件
        # id,name,num为返回结果res，类型为一个dict
        # 如果need_loc，则res中增加各种loc,new_loc,count_loc字段
        elif table_name in cls.ALI_LOG_STORE:
            from_time, to_time = cls._get_alilog_time_str()
            if not expression:
                resp_set = cls.CACHED_ALI_LOG
            else:
                expression = expression.replace('=', ':')
                expression = expression.replace(',', " and ")
                resp_set = AliLogService.get_all_log_by_time_and_topic(from_time=from_time, to_time=to_time,
                                                                       query=expression)
            cnt = 0

            for resp in resp_set:
                tmp_cnt = resp.get_count()
                if tmp_cnt:
                    cnt += resp.get_count()
                # 对每个location，在loc_cnts这个dict中，存三个字段，loc,new_loc,count_loc
                # 只对有count且不大于1000000的才进行分location统计
                if cnt and cnt < 1000000:
                    new_user_acted = set()
                    # 遍历满足统计量限制的结果集
                    for log in resp.logs:
                        contents = log.get_contents()
                        user_id = contents['user_id']
                        cls.cal_res_by_uid(user_id, res, new_user_acted)
            res[0]['计数'] = cnt
        # 如果该统计量需要的信息都在某一表内，且该表在数据库里，其表达式expression与上一种情况格式不同，可有可无；
        # 有expression时，其包含若干字段，每一个字段作为一个检索数据库的限制条件
        # id,name,num为返回结果res，类型为一个dict
        # 如果need_loc，则res中增加各种loc,new_loc,count_loc字段
        else:
            time_str = cls._get_time_str(table_name, judge_field)
            expression = '' if not expression else expression
            if not cls.IS_TESTING:
                if item.name in [u'警告数']:
                    exc_str = 'len(%s.objects(%s,%s).distinct(\'user_id\'))' % (table_name, time_str, expression)
                else:
                    exc_str = '%s.objects(%s,%s).count()' % (table_name, time_str, expression)
            else:
                exc_str = '%s.objects(%s,%s).limit(1000).count()' % (table_name, time_str, expression)
            # cnt表示一天时间内，满足该统计量限制的记录个数
            cnt = eval(exc_str)
            if not cnt:
                cnt = 0
            res[0]['计数'] = cnt
            table_user_id = {
                "Report": "target_uid",
                "Feedback": "uid"
            }
            if item.name in [u'警告数']:
                eval_str = 'TrackSpamRecord.objects(%s,%s).distinct(\'user_id\')' % (time_str, expression)
                new_user_acted = set()
                for user_id in eval(eval_str):
                    cls.cal_res_by_uid(user_id, res, new_user_acted)
            # 对每个location，在loc_cnts这个dict中，存三个字段，loc,new_loc,count_loc
            # 只对有count且不大于1000000的才进行分location统计
            elif cnt and cnt < 1000000:
                eval_str = '%s.objects(%s,%s)' % (table_name, time_str, expression)
                if cls.IS_TESTING:
                    eval_str += '.limit(1000)'
                new_user_acted = set()
                # 遍历满足统计量限制的结果集
                for obj in eval(eval_str):
                    if table_name == 'User':
                        user_id = str(obj.id)
                    elif table_name in table_user_id:
                        user_id = getattr(obj, table_user_id[table_name])
                        # user_id = str(obj.target_uid)
                    else:
                        user_id = obj.user_id
                    cls.cal_res_by_uid(user_id, res, new_user_acted)

        cls.CACHED_RES[item_id] = res
        return res

    @classmethod
    def delete_stat_item(cls, item_id):
        StatItems.objects(id=item_id).delete()
        return None, True

    @classmethod
    def out_port_result(cls, dst_addr, date, stat_type=StatItems.BUSINESS_TYPE):
        if not cls.USER_LOC:
            cls.load_user_loc()
            print('load user location succ', cls.LOC_STATED)
        if not cls.USER_GEN:
            cls.load_user_gen()
            print('load user gender succ', cls.GENDERS)
        res_lst = [[] for i in range(len(cls.LOC_STATED) + 1)]
        cls.DATE_DIS = datetime.timedelta(hours=0)
        # 遍历StatItems中所有类型为stat_type的统计量item
        for item in StatItems.get_items_by_type(stat_type):
            try:
                # res为根据该统计量的id计算得到的结果
                if not str(item.id) == '5e12e7bf3fff22086bdc6e7f':
                    continue
                print(item.name)
                res = cls.cal_by_id(str(item.id))
                for sheet_index in range(len(res)):
                    sheet = res[sheet_index]
                    temp_res = [sheet['name'], sheet['计数'], sheet['boy'], sheet['girl'], sheet['新用户人次'], sheet['新用户人数']]
                    res_lst[sheet_index].append(temp_res)
            except Exception as e:
                # print(e)
                continue
        write_data_to_multisheets(dst_addr, ['总计'] + cls.LOC_STATED, ['名称', '计数', 'boy', 'girl', '新用户人次', '新用户人数'],
                                  res_lst)
