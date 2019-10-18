# coding: utf-8
import time
from ..model import (
    User,
    Feed,
    HuanxinAccount,
)
from ..service import (
    SmsCodeService,
    UserService,
    AnoyMatchService,
    HuanxinService,
    FeedService
)
from ..const import (
    GIRL,
    BOY
)
from ..key import (
    REDIS_MATCH_BEFORE_PREFIX,
)

from hendrix.conf import setting
from ..redis import RedisClient


redis_client = RedisClient()['lit']

class DebugHelperService(object):
    BASE_PHONE = 8618189180000
    TEST_NUM = 20

    @classmethod
    def get_field_by_batchid(cls, bid, field):
        if field == 'gender':
            return GIRL if bid < cls.TEST_NUM/2 else BOY
        if field == 'zone_phone':
            return str(cls.BASE_PHONE + bid)
        if field == 'birthdate':
            return '2000-01-01'
        if field == 'nickname':
            return 'test-nick%d' % bid
        if field == 'avatar':
            return 'c05f00c6-40a7-11e9-b1c7-00163e02deb4'
        if field == 'huanxin':
            return HuanxinAccount.create(*HuanxinService.gen_id_pwd())

    @classmethod
    def batch_create_login(cls):
        fields = ['nickname', 'avatar', 'gender', 'birthdate', 'huanxin', 'zone_phone']
        res = []
        for _ in range(cls.TEST_NUM):
            zone_phone = cls.get_field_by_batchid(_, 'zone_phone')
            zone = zone_phone[:2]
            phone = zone_phone[2:]
            user = User.get_by_phone(zone_phone)
            if not user:
                attrs = [cls.get_field_by_batchid(_, el) for el in fields]
                user = User.create_by_phone(*attrs)
            code = '8888'
            SmsCodeService.send_code(zone, phone)
            res.append(UserService.phone_login(zone, phone, code)[0])
        return res

    @classmethod
    def batch_anoy_match_start(cls):
        res = []
        for _ in range(cls.TEST_NUM):
            zone_phone = cls.get_field_by_batchid(_, 'zone_phone')
            user = User.get_by_phone(zone_phone)
            res.append(AnoyMatchService.create_fakeid(str(user.id)))
        return res

    @classmethod
    def del_match_before(cls, user_id=None):
        for k in redis_client.keys():
            if REDIS_MATCH_BEFORE_PREFIX in k:
                if not user_id:
                    redis_client.delete(k)
                else:
                    if user_id in k:
                        redis_client.delete(k)

    @classmethod
    def feed_num(cls, user_id):
        return 3


    @classmethod
    def debug_all_keys(cls, key=None):
        res = {'time_now': int(time.time())}
        for k in redis_client.keys():
            if key and key not in k:
                continue
            if 'cache' in k:
                continue
            try:
                res[k] = redis_client.get(k)
            except:
                res[k] = redis_client.zscan(k)[1]
        if not key:
            users = []
            for _ in User.objects().order_by('-create_time'):
                raw_info, status = UserService.get_user_info(str(_.id), str(_.id))
                if status:
                    raw_info['phone'] = _.phone
                    users.append(raw_info)
            res['zusers'] = users
            feeds = []
            for _ in Feed.objects().order_by('-create_time'):
                feeds.append(FeedService.get_feed_info(None, str(_.id)))
            res['zzfeeds'] = feeds
        return res