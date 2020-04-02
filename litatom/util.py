# encoding=utf8
import base64
import datetime
import decimal
import functools
import hashlib
import logging
import os
import random
import re
import time
import urllib
import urlparse
import math
import codecs

from flask import request
from hendrix.conf import setting
from hendrix.util import get_hostname
from pyparsing import anyOpenTag, anyCloseTag

import json
from . import const

logger = logging.getLogger(__name__)


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError, e:
        return False
    return True


def get_args_from_db(db_name):
    db_m = setting.DB_SETTINGS.get(db_name)
    ''''host': u'mongodb://ll:11@172.31.138.46/lit?authsource=lit','''
    port = db_m['port']
    conn_url = db_m['host']
    user_pwd = conn_url.split('://')[1].split('@')[0]
    user, pwd = user_pwd.split(':')
    host = conn_url.split('@')[1].split('/')[0]
    db = conn_url.split("=")[-1]
    return host, port, user, pwd, db


def passwdhash(passwd):
    m = hashlib.md5()
    m.update(passwd)
    m.update('hello world')
    return m.hexdigest()

def ensure_path(path):
    dir_name  = path[:path.rfind('/')]
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

def exists_path(path):
    dir_name = path[:path.rfind('/')]
    return os.path.exists(dir_name)

def ensure_unicode(v):
    if isinstance(v, str):
        v = v.decode('utf8')
    return unicode(v)  # convert anything not a string to unicode too


def get_zero_today():
    now = datetime.datetime.now()
    return datetime.datetime(year=now.year, month=now.month, day=now.day)


def trunc(v, length):
    v = ensure_unicode(v).encode('utf8')
    if len(v) > length:
        return v.decode('utf-8')[:length].encode('utf-8')
    return v


def format_standard_date(time_data):
    """datetime -> string"""
    return time_data.strftime('%Y-%m-%d')


def format_standard_time(time_data):
    """datetime -> string"""
    return time_data.strftime('%Y-%m-%d %H:%M:%S')


def trans_secs_to_time(secs):
    """秒数 -> string %H:%M:%S"""
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return "%d:%02d:%02d" % (h, m, s)
    return "%02d:%02d" % (m, s)


def parse_standard_time(time_data_str):
    """str -> datetime"""
    return datetime.datetime.strptime(time_data_str, '%Y-%m-%d %H:%M:%S')

def get_ts_from_str(time_str):
    """str -> timestamp(int)"""
    return time.mktime(time.strptime(time_str, "%Y-%m-%d %H:%M:%S"))


def next_date(d_time, d=1):
    """datetime -> datetime"""
    return d_time + datetime.timedelta(days=d)


def get_times_from_str(time_data_str):
    """str -> datetime"""
    if len(time_data_str) == 8:
        d_time = datetime.datetime.strptime(time_data_str, '%Y%m%d')
    else:
        d_time = datetime.datetime.strptime(time_data_str, '%Y%m%d%H%M%S')
    return date_to_int_time(d_time), d_time


def parse_standard_date(time_data_str):
    """str -> datetime"""
    return datetime.datetime.strptime(time_data_str, '%Y-%m-%d')


def time_str_by_ts(ts):
    """timestamp(int) -> str"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def date_to_int_time(d):
    """datetime -> timestamp(int)"""
    return int(time.mktime(d.timetuple()))


def get_time_info(int_time, user_mode=False):
    time_now = int(time.time())
    time_dis = time_now - int_time
    if time_dis < const.ONE_MIN:
        time_desc = 'now' if not user_mode else 'active'
    elif time_dis < const.ONE_HOUR:
        mins = time_dis/const.ONE_MIN
        time_desc = '1 minute ago' if mins == 1 else '%d mins ago' % mins 
    elif time_dis < const.ONE_DAY:
        hours = time_dis/const.ONE_HOUR
        time_desc = '1 hour ago' if hours == 1 else '%d hours ago' % hours
    else:
        days = time_dis/const.ONE_DAY
        if not user_mode:
            time_desc = '1 day ago' if days == 1 else '%d days ago' % days
        else:
            time_desc = '%d day ago' % days if days <= 3 else '%d days ago' % 3
    return {
        'time': int_time,
        'time_desc': time_desc
    }


def now_date_key():
    """今日日期str"""
    return datetime.datetime.now().strftime('%Y-%m-%d') # for time latency reason


def low_high_pair(id1, id2):
    return id1 + id2 if id1 < id2 else id2 + id1

def unix_ts_string(ts):
    """timestamp(int) -> str"""
    time_array = time.localtime(ts)
    return time.strftime("%Y-%m-%d %H:%M", time_array)


def unix_ts_local(time_data):
    """datetime -> local timestamp(int)"""
    try:
        ts = int(time.mktime(time_data.timetuple()))
        return ts
    except Exception:
        return 0


def unix_ts_utc(dt):
    """datetime -> utc timestamp(int)"""
    try:
        ts = int(time.mktime(dt.utctimetuple()))
        return ts
    except Exception:
        return 0


def date_from_unix_ts(ts):
    """timestamp(int) -> datetime"""
    try:
        return datetime.datetime.fromtimestamp(ts)
    except Exception:
        return None


def is_emoji(schar):
    if u'\ud800' <= schar <= u'\udbff':
        return True
    elif u'\u2100' <= schar <= u'\u27ff':
        return True
    elif u'\u2b05' <= schar <= u'\u2b07':
        return True
    elif u'\u2934' <= schar <= u'\u2935':
        return True
    elif u'\u3297' <= schar <= u'\u3299':
        return True
    elif schar in [u'\u00a9', u'\u00ae', u'\u303d', u'\u3030', u'\u2b55', u'\u2b1c', u'\u2b1b', u'\u2b50']:
        return True
    return False

'''
从xlsx文件name中读取第一张表，返回list: tb_heads, 为表中第一行；返回list[list]: data，为表中各行 
'''
def read_data_from_xls(name):
    import xlrd
    tb = xlrd.open_workbook(name).sheets()[0]
    tb_heads = tb.row_values(0)
    nrows = tb.nrows-1
    data = []
    for row in range(nrows):
        data.append(tb.row_value(row+1))
    return tb_heads,data


def write_data_to_xls(name, tb_heads, datas):
    """表头在第一行"""
    import xlwt
    f = xlwt.Workbook(encoding='utf-8')
    sheet1 = f.add_sheet(name.split('/')[-1], cell_overwrite_ok=True)
    for i in range(len(tb_heads)):
        sheet1.write(0, i, tb_heads[i])
    if not isinstance(datas[0], list):
        datas = [datas]
    for i in range(len(datas)):
        for j in range(len(datas[i])):

            sheet1.write(i + 1, j, datas[i][j])
    f.save(name)

def write_data_to_multisheets(name, sheet_names, tb_heads, data):
    """

    :param name:
    :param sheet_names:
    :param tb_heads:
    :param data:一个列表，列表中的每个元素也是一个列表，每个元素都是1个sheet中的数据
    :return:
    """
    import xlwt
    f = xlwt.Workbook(encoding='utf-8')
    # 建表
    sheets = [f.add_sheet(s) for s in sheet_names]
    # 写表头
    for sheet in sheets:
        for i in range(len(tb_heads)):
            sheet.write(0, i, tb_heads[i])
    for sheet_num in range(len(data)):
        sheet_data = data[sheet_num]
        for i in range(len(sheet_data)):
            for j in range(len(sheet_data[i])):
                sheets[sheet_num].write(i+1, j, sheet_data[i][j])
    f.save(name)


def write_data_to_xls_col(name, tb_heads, data, encoding='ascii'):
    """表头在第一列"""
    import xlwt
    f = xlwt.Workbook(encoding=encoding)
    sheet1 = f.add_sheet(name.split('/')[-1], cell_overwrite_ok=True)
    for i in range(len(tb_heads)):
        sheet1.write(i, 0, tb_heads[i])
    if not isinstance(data[0], list):
        datas = [data]
    for i in range(len(data)):
        for j in range(len(data[i])):
            sheet1.write(j, i+1, data[i][j])
    f.save(name)

def write_sheet_certain_pos(sheet_name, row_pos, col_pos, data):
    """向excel sheet具体位置中写入数据"""
    sheet_name.write(row_pos, col_pos, data)

def remove_emoji_ending(raw_string):
    formated_string = '\n'.join([x.strip() for x in raw_string.replace('\r', '\n').split('\n') if x])
    while len(formated_string) > 0 and is_emoji(formated_string[-1]):
        formated_string = formated_string[:-1]
    return formated_string

def dic_order_by_value(d, reverse=False):
    """字典按值排序"""
    d_order=sorted(d.items(),key=lambda x:x[1],reverse=reverse)
    return d_order


# 暂未被使用，放在这里供参考. 因为除了汉字还有各国语言非英文字符要考虑.
def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
        return True
    else:
        return False


def is_number(uchar):
    """判断一个unicode是否是数字"""
    if uchar >= u'\u0030' and uchar <= u'\u0039':
        return True
    else:
        return False


def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    if (uchar >= u'\u0041' and uchar <= u'\u005a') or (uchar >= u'\u0061' and uchar <= u'\u007a'):
        return True
    else:
        return False

def str2float(str):
    """转换str中第一个浮点数，没有数返回None"""
    pattern = '[0-9]+\.[0-9]+'
    res = re.search(pattern, str)
    if res:
        res = res.span()
        return float(str[res[0]:res[1] - 1])
    return None


def dsn2srv(dsn):
    parsed = urlparse.urlparse(dsn)
    return parsed.hostname, parsed.port

def rm_file(file):
    os.remove(file)

def write_to_json(file, dic):
    """
    写入一个json类型的文件
    :param dic: 一个字典的list，要求其中的字典都是可以json序列化的
    """
    if exists_path(file):
        rm_file(file)
    with codecs.open(file,'a',encoding='utf-8') as f:
        for item in dic:
            f.write(json.dumps(item, indent=4, ensure_ascii=False))
            f.write('\n')

def find_key_by_value(dic, value):
    """从字典的值反查键，值必须唯一"""
    return list(dic.keys())[list(dic.values()).index(value)]

class CachedProperty(object):
    """Decorator like python built-in ``property``, but it results only
    once call, set the result into decorated instance's ``__dict__`` as
    a static property.
    """

    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        val = inst.__dict__[self.fn.__name__] = self.fn(inst)
        return val


cached_property = CachedProperty  # alias


class EnvvarReader(dict):
    __uninitialized = object()

    def __init__(self, *envvars):
        for ev in envvars:
            ev_norm = self._normalize(ev)
            if ev != ev_norm:
                raise ValueError('invalid envvar name: {!r}'.format(ev))
            dict.__setitem__(self, ev_norm, self.__uninitialized)

    @cached_property
    def configured(self):
        return any([self[k] for k in self])

    def _normalize(self, varname):
        return varname.strip()

    def __getitem__(self, key):
        key = self._normalize(key)
        value = dict.__getitem__(self, key)
        if value is self.__uninitialized:
            value = os.getenv(key, None)
            dict.__setitem__(self, key, value)
        return value

    __getattr__ = __getitem__

    def get(self, key, default=None):
        val = self.__getitem__(key)
        if val is not None:
            return val
        return default

    def get_int(self, key, default=None):
        value = self.__getitem__(key)
        if value is not None:
            return int(value)
        return default

    def get_float(self, key, default=None):
        value = self.__getitem__(key)
        if value is not None:
            return float(value)
        return default

    def get_bool(self, key, default=False):
        value = self.__getitem__(key)
        if value not in (None, 0):
            return True
        return default

    def get_json(self, key, default=None):
        value = self.__getitem__(key)
        if value is not None:
            return json.loads(value)
        default = default or {}
        return default

    def __setitem__(self, key, value):
        raise RuntimeError('setting envvar not supported')

    __setattr__ = __setitem__


class BaseDBManager(dict):
    @property
    def settings(self):
        raise NotImplementedError()

    def _initdb(self, name):
        raise NotImplementedError()

    def initdb(self, name):
        if not self.get(name):
            self._initdb(name)
        else:
            logger.warning('db: %r already inited', name)

    def initall(self):
        for db in self.settings:
            self.initdb(db)

    def __getitem__(self, key):
        if key not in self and key in self.settings:
            self.initdb(key)
        return super(BaseDBManager, self).__getitem__(key)

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError:
            raise AttributeError(name)


class EnumItem(object):
    def __init__(self, name, value, display=u''):
        self.name = name
        self.value = value
        self.display = display

    def __str__(self):
        return self.display.encode('utf-8')

    def __repr__(self):
        if self.display:
            r = u'EnumItem({0.name}): <{0.value}, {0.display}>'.format(self)
        else:
            r = u'EnumItem({0.name}): <{0.value}>'.format(self)
        return r.encode('utf-8')


class Enum(object):
    def __init__(self, *items):
        self._items = {}
        values = []
        for i in items:
            display = ''
            if len(i) == 2:
                name, value = i
            elif len(i) == 3:
                name, value, display = i
            else:
                raise ValueError(i)
            if value in values:
                raise ValueError('duplicate value: {!r}'.format(value))
            values.append(value)
            i = EnumItem(name, value, display)
            self._items[name] = i

    def __repr__(self):
        return 'Enum: <{}>'.format(', '.join(self._items.keys()))

    def __getattr__(self, name):
        try:
            return self._items[name].value
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, key):
        return self._items[key].value

    def items(self):
        return self._items.values()

    def values(self):
        return set([i.value for i in self._items.values()])

    def get_by_value(self, val):
        for v in self.items():
            if v.value == val:
                return v
        raise ValueError('invalid value: {!r}'.format(val))


class GeoCoord(object):
    COORD_SYSTEM_GPS = 1
    COORD_SYSTEM_TENCENT_AMAP = 2
    COORD_SYSTEMS = [
        COORD_SYSTEM_GPS,
        COORD_SYSTEM_TENCENT_AMAP,
    ]

    _decimal_ctx = decimal.getcontext().copy()
    _decimal_ctx.prec = 8
    _decimal_exponent = decimal.Decimal('.00001')

    def __init__(self, lat, lng, sys=COORD_SYSTEM_GPS):
        with decimal.localcontext(self._decimal_ctx) as ctx:
            self.lat = ctx.create_decimal(lat).quantize(self._decimal_exponent)
            self.lng = ctx.create_decimal(lng).quantize(self._decimal_exponent)
        if sys not in self.COORD_SYSTEMS:
            raise ValueError('invalid coord system: {!r}'.format(sys))
        self.sys = sys

    def dump(self):
        return '{},{}'.format(self.lat, self.lng)


def update_image_protocol(img, use_https=False):
    protocol = 'https:' if use_https else 'http:'
    img = re.sub(r'^http:', protocol, img)
    return img


def image_update_item(item, size=80):
    if 'image' in item:
        img = item['image']
        img = update_image_protocol(img)
        item['image'] = img + '?wm=%d&hm=%d&q=92' % (size, size)


def image_update(a, size=80):
    if isinstance(a, dict):
        image_update_item(a['user'], size=size)
    if isinstance(a, list):
        for i in a:
            image_update(i, size=size)
    return a


def remove_null_chars(s):
    """
    移除NULL字符
    """
    if not s:
        return ''
    return s.replace(chr(0), '')


def remove_continuous_blanks(s):
    """
    将一段文本中连续的空白字符都变成一个半角空格
    """
    if not s:
        return ''
    return re.sub(r'\s+', ' ', s, flags=re.UNICODE)


def validate_phone_number(phone, zone=None):
    '''
    验证是不是一个合法的中国手机号码.
    '''
    try:
        phone = str(phone).replace('+', '')
    except Exception:
        return None

    if not phone.isdigit():
        return None

    # if len(phone) == 11 and phone.startswith('1') and zone == 86:
    #     phone = '86' + phone

    if len(phone) == 13:
        return phone
    return phone

def normalize_cache_key(text):
    """
    cmem要求key里不能出现空白字符，并且key最大长度250字节
    因此将可能非法的内容转成md5
    :param key: cache key
    :return: md5 str
    """
    if isinstance(text, unicode):
        text = text.encode('utf8')

    return hashlib.md5(text).hexdigest()


def memoize(f):
    _res_mapping = {}

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        key = args + tuple(sorted(kwargs.items()))
        try:
            return _res_mapping[key]
        except KeyError:
            _res_mapping[key] = value = f(*args, **kwargs)
            return value

    return wrapper


@memoize
def on_staging():
    """查看当前是否在Staging环境"""
    return True
    return get_hostname() in (
        'sns-litatom-staging',
        'sns-litatom-staging02',
    )


@memoize
def in_container():
    return False
    # from hendrix.conf import setting
    # return setting.IN_CONTAINER


def filter_script_tag(s):
    """
    html tag 过滤器
    :param s: 进行检测的文本
    :return: 脱去所有tag之后的文本
    """
    stripper = (anyOpenTag | anyCloseTag).suppress()
    after = stripper.transformString(s)
    while after != s:
        s = after
        after = stripper.transformString(s)
    return s


class ExpoBackoffDecorr(object):
    def __init__(self, base, cap):
        self.base = base
        self.cap = cap
        self.sleep = self.base

    def backoff(self, n):
        self.sleep = min(self.cap, random.uniform(self.base, self.sleep * 3))
        return self.sleep


def parse_image_fileid(url):
    """
    从腾讯云图片url中解析出文件id
    :param url: 形如 http://ci.litatom.com/fileid...
    """
    if not url:
        return ''

    s = re.search(r'(https?:)?//ci\.litatom\.com/([^@?]+)', url)
    if s:
        return s.group(2)

    return ''


def image_url_to_origin(url):
    """
    将腾讯云图片链接转换成原始形式 ci.litatom.com/fileid
    """
    fileid = parse_image_fileid(url)
    if fileid:
        return setting.QCLOUD_IMAGE_HOST + fileid

    return url


def parse_video_fileid(url):
    """
    从七牛视频url中解析出文件id
    :param url: 形如 http://v.litatom.com/fileid...
    """
    if not url:
        return ''

    s = re.search(r'(https?:)?//(v|(sa)|(sg))\.litatom\.com/([^?]+)', url)
    if s:
        return s.group(5)

    return ''


def remove_image_protocol(url):
    if not url:
        return ''
    return url.replace('http://', '//').replace('https://', '//')


def resize_pic_by_device(url, device_resolution, platform):
    """
    根据客户端设备信息，调整图片尺寸
    :param url: 以ci.litatom.com开头的图片链接
    :param device_resolution: 一个tuple，表示设备分辨率
    :param platform: ios / android
    """
    short_edge, long_edge = device_resolution
    if not (url and short_edge > 0 and long_edge > 0):
        return url
    if short_edge > long_edge:
        short_edge, long_edge = long_edge, short_edge

    for limit in (120, 240, 320, 640, 750, 1080, 1280):
        if short_edge <= limit:
            break
    # 对iPhone特殊处理
    if platform == const.PLATFORM_IOS and limit == 1280:
        limit = 1080

    return resize_ci_image(url, limit)


def remove_non_words(text):
    """
    移除所有non-word字符，支持unicode
    :param text:
    :return:
    """
    if not text:
        return ''

    return re.sub(r'\W', '', text, flags=re.UNICODE)


def add_query_to_url(url, key, value):
    """
    给一个url加上指定参数
    """
    if not (url and key):
        return url
    new_query = '%s=%s' % (key, value)
    url = urllib.unquote(url)
    up = urlparse.urlparse(url)
    path = up.path
    p_query = up.query
    if p_query:
        query_part = "?" + p_query + "&" + new_query
    else:
        query_part = "?" + new_query
    return up.scheme + "://" + up.netloc + urllib.quote(path, safe="/") + query_part


def calculate_distance(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    Source: https://gis.stackexchange.com/a/56589/15183
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    km = 6371 * c
    return km
