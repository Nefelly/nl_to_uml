# coding: utf-8
import datetime
import logging
import collections
import xlwt
from ..model import (
    Feed,
    User,
)
from ..util import (
    next_date,
    date_to_int_time,
    find_key_by_value,
    now_date_key,
    parse_standard_date,
    format_standard_date,
    write_sheet_certain_pos,
    get_zero_today,
)
from ..service import (
    AliLogService,
)

from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']


class RetainAnaService(object):
    '''
    用户留存数据信息服务
    '''
    IS_TESTING = False
    USER_LOC = {}
    LOC_STATED = ['TH', 'VN']
    CACHED_RES = {}

    COUNTRY_ENCODE = {'VN': 1, 'TH': 2, 'ID': 3}
    GENDER_ENCODE = {'boy': 1, 'girl': 2}
    ACTION_QUERY = {'startMatch': 'action:match and remark:startMatch'}
    ACTION_ENCODE = {'startMatch': 1, 'feed_create': 101}

    @classmethod
    def _load_user_action_info(cls, date, user_info, action):
        action_code = cls.ACTION_ENCODE[action]
        resp_set = AliLogService.get_log_by_time_and_topic(from_time=AliLogService.datetime_to_alitime(date),
                                                           to_time=AliLogService.datetime_to_alitime(
                                                               next_date(date, 1)),
                                                           project='litatomaction', logstore='litatomactionstore',
                                                           query=cls.ACTION_QUERY[action])
        for resp in resp_set:
            for log in resp.logs:
                contents = log.get_contents()
                user_id = contents['user_id']
                if user_id in user_info.keys():
                    user_info[user_id][3].add(action_code)

    @classmethod
    def _load_user_info(cls, date):
        """
        将指定日期的用户数据load到user_info字典中
        :param date: datetime类型  表示0点
        :return:
        """
        print('in _load_user_info', date)
        user_info = {}
        from_ts = date_to_int_time(date)
        to_ts = date_to_int_time(next_date(date, 1))
        users = User.objects(create_time__gte=date, create_time__lte=next_date(date,1), platform='android')

        for user in users:
            user_id = str(user.id)
            user_info[user_id] = []

            loc = user.country
            if loc and loc in cls.COUNTRY_ENCODE:
                user_info[user_id].append(cls.COUNTRY_ENCODE[loc])
            else:
                user_info[user_id].append(0)

            gender = user.gender
            if gender and gender in cls.GENDER_ENCODE:
                user_info[user_id].append(cls.GENDER_ENCODE[gender])
            else:
                user_info[user_id].append(0)

            age = User.age_by_user_id(user_id)
            if age and 13 <= age <= 25:
                user_info[user_id].append(age)
            else:
                user_info[user_id].append(0)

            user_info[user_id].append(set())

        feeds = Feed.get_by_create_time(from_ts, to_ts)
        feed_create_code = cls.ACTION_ENCODE['feed_create']
        for feed in feeds:
            if feed.user_id in user_info:
                user_info[feed.user_id][3].add(feed_create_code)

        for action in cls.ACTION_QUERY:
            cls._load_user_action_info(date, user_info, action)
        return user_info

    @classmethod
    def get_new_user_info(cls, date):
        """返回特定日期的新用户信息"""
        user_info = cls._load_user_info(date)
        return user_info

    @classmethod
    def get_retain_res(cls, addr, from_date=next_date(get_zero_today(), -31), to_date=next_date(get_zero_today(), -1)):
        info_basic_list = []  # 存储了每日的新用户info
        res_basic_list = []  # 存储了每日新用户数据统计
        res_list = collections.OrderedDict()  # 存储了每日之后的次日留存、7日留存、30日留存
        temp_date = from_date
        while temp_date <= to_date:
            date_info = cls.get_new_user_info(temp_date)
            info_basic_list.append(date_info)
            date_res = cls.get_res_from_user_info(date_info)
            res_basic_list.append(date_res)
            temp_date += datetime.timedelta(days=1)

        # 计算留存
        for i in range(len(info_basic_list)):
            current_date = next_date(from_date, i)
            res_list[format_standard_date(current_date)] = [
                cls.get_certain_day_retain_res(current_date, info_basic_list[i], 1),
                cls.get_certain_day_retain_res(current_date, info_basic_list[i], 7),
                cls.get_certain_day_retain_res(current_date, info_basic_list[i], 30)]

        cls.write_retain_res_to_excel(addr, res_list, res_basic_list)

    @classmethod
    def write_retain_res_to_excel(cls, addr, res, basic_date_res):
        wb = xlwt.Workbook(encoding='utf-8')
        worksheet = [wb.add_sheet('总数',cell_overwrite_ok=True), wb.add_sheet('boy',cell_overwrite_ok=True), wb.add_sheet('girl',cell_overwrite_ok=True),
                     wb.add_sheet('未知性别',cell_overwrite_ok=True), wb.add_sheet('VN',cell_overwrite_ok=True), wb.add_sheet('TH',cell_overwrite_ok=True),
                     wb.add_sheet('ID',cell_overwrite_ok=True), wb.add_sheet('其它地区',cell_overwrite_ok=True)]
        for action in cls.ACTION_ENCODE:
            worksheet.append(wb.add_sheet(action,cell_overwrite_ok=True))
        for age in range(13, 26):
            worksheet.append(wb.add_sheet('age' + str(age),cell_overwrite_ok=True))
        worksheet.append(wb.add_sheet(u'其它年龄',cell_overwrite_ok=True))

        # 在每一行前面写入日期表头
        i = 1
        for date in res:
            for sheet in worksheet:
                write_sheet_certain_pos(sheet, i, 0, date)
            i += 1

        # 在每一列前面写入项目表头
        for sheet in worksheet:
            write_sheet_certain_pos(sheet, 0, 0, u'留存率/留存人数')
            write_sheet_certain_pos(sheet, 0, 1, u'当日新增用户人数')
            write_sheet_certain_pos(sheet, 0, 2, u'次日留存')
            write_sheet_certain_pos(sheet, 0, 3, u'7日留存')
            write_sheet_certain_pos(sheet, 0, 4, u'30日留存')

        # 分日期（行）写入具体数据
        i = 0
        for date in res:
            # 分不同间隔的time interval（列）写入数据
            for j in range(0, 3):
                if not res[date][j]:
                    continue
                base_res = basic_date_res[i]
                # 分不同的表写入数据
                for sheet in worksheet:
                    if not base_res[sheet.name]:
                        write_sheet_certain_pos(sheet, i + 1, j + 2, 0)
                    else:
                        write_sheet_certain_pos(sheet, i + 1, 1, str(base_res[sheet.name]))
                        write_sheet_certain_pos(sheet, i + 1, j + 2,
                                                str(res[date][j][sheet.name] / float(base_res[sheet.name])) + '/' + str(
                                                    res[date][j][sheet.name]))
            i += 1
        wb.save(addr)

    @classmethod
    def get_certain_day_retain_res(cls, basic_date, basic_info, days=1):
        now = datetime.datetime.now()
        retain_date = next_date(basic_date, days)
        if retain_date > now:
            return None
        retain_user_info = cls.get_retain_user_info(retain_date, basic_info)
        retain_res = cls.get_res_from_user_info(retain_user_info)
        return retain_res

    @classmethod
    def get_retain_user_info(cls, date, user_info):
        """获得留存用户"""
        resp_set = AliLogService.get_log_by_time_and_topic(from_time=AliLogService.datetime_to_alitime(date),
                                                           to_time=AliLogService.datetime_to_alitime(
                                                               next_date(date, 1)),
                                                           query='*| select distinct user_id limit 5000000')
        res_user_info = {}
        for resp in resp_set:
            for log in resp.logs:
                contents = log.get_contents()
                user_id = contents['user_id']
                if user_id in user_info:
                    res_user_info[user_id] = user_info[user_id]
        return res_user_info

    @classmethod
    def get_res_from_user_info(cls, user_info):
        """从用户信息中获得统计信息"""
        res = {u'总数': len(user_info)}
        for item in cls.GENDER_ENCODE:
            res[item] = 0
        for item in cls.COUNTRY_ENCODE:
            res[item] = 0
        for item in cls.ACTION_ENCODE:
            res[item] = 0
        for age in range(13, 26):
            res['age' + str(age)] = 0
        res[u'其它年龄'] = 0
        res[u'其它地区'] = 0
        res[u'未知性别'] = 0

        for user in user_info:
            # location
            if user_info[user][0] in cls.COUNTRY_ENCODE.values():
                res[find_key_by_value(cls.COUNTRY_ENCODE, user_info[user][0])] += 1
            else:
                res[u'其它地区'] += 1

            # gender
            if user_info[user][1] in cls.GENDER_ENCODE.values():
                res[find_key_by_value(cls.GENDER_ENCODE, user_info[user][1])] += 1
            else:
                res[u'未知性别'] += 1

            # age
            if 'age' + str(user_info[user][2]) in res:
                res['age' + str(user_info[user][2])] += 1
            else:
                res[u'其它年龄'] += 1

            # action
            for action_code in user_info[user][3]:
                res[find_key_by_value(cls.ACTION_ENCODE, action_code)] += 1

        return res
