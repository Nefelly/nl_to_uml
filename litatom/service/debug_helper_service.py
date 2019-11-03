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
from ..util import (
    low_high_pair,
    now_date_key
)
from ..key import (
    REDIS_MATCH_BEFORE_PREFIX,
    REDIS_VIDEO_MATCHED_BEFORE,
    REDIS_VOICE_MATCHED_BEFORE,
    REDIS_MATCH_BEFORE,
    REDIS_USER_MATCH_LEFT,
    REDIS_USER_VIDEO_MATCH_LEFT,
    REDIS_USER_VOICE_MATCH_LEFT
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
    def get_fakeid_by_uid(cls, user_id):
        return AnoyMatchService._get_anoy_id(User.get_by_id(user_id))[0]


    @classmethod
    def del_match_before(cls, user_id=None):
        if user_id:
            fakeid = cls.get_fakeid_by_uid(user_id)
        for k in redis_client.keys():
            if REDIS_MATCH_BEFORE_PREFIX in k:
                if not user_id:
                    redis_client.delete(k)
                else:
                    if fakeid in k:
                        redis_client.delete(k)

    @classmethod
    def online_del_match_status(cls, user_id1, user_id2):
        def del_times_left(user_id):
            if not user_id:
                return
            now_date = now_date_key()
            redis_client.delete(REDIS_USER_MATCH_LEFT.format(user_date=user_id + now_date))
            redis_client.delete(REDIS_USER_VOICE_MATCH_LEFT.format(user_date=user_id + now_date))
            redis_client.delete(REDIS_USER_VIDEO_MATCH_LEFT.format(user_date=user_id + now_date))

        def del_low_high_pair(pair):
            if not pair:
                return
            redis_client.delete(REDIS_MATCH_BEFORE.format(low_high_fakeid=pair))
            redis_client.delete(REDIS_VOICE_MATCHED_BEFORE.format(low_high_fakeid=pair))
            redis_client.delete(REDIS_VIDEO_MATCHED_BEFORE.format(low_high_fakeid=pair))
        if not user_id1:
            return u'phone1 not exists, starts with86 please', False
        del_times_left(user_id1)
        if not user_id2:
            return u'phone2 not exists, starts with86 please', False
        fake_id1 = cls.get_fakeid_by_uid(user_id1)
        fake_id2 = cls.get_fakeid_by_uid(user_id2)
        pair = low_high_pair(fake_id1, fake_id2)
        del_low_high_pair(pair)
        return None, True

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
                try:
                    res[k] = redis_client.zscan(k)[1]
                except:
                    res[k] = str(redis_client.smembers(k))
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