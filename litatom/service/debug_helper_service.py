# coding: utf-8
from ..redis import RedisClient
from ..model import (
    User,
    HuanxinAccount,
)
from ..service import (
    SmsCodeService,
    UserService,
    AnoyMatchService,
    HuanxinService
)
from ..const import (
    GIRL,
    BOY
)

class DebugHelperService(object):
    BASE_PHONE = 8618189180000
    TEST_NUM = 20

    @classmethod
    def get_field_by_batchid(cls, bid_field):
        bid = bid_field[0]
        field = bid_field[1]
        if field == 'gender':
            gender = GIRL if bid < cls.TEST_NUM/2 else BOY
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
        fields = ['nickname', 'avatar', 'gender', 'birthdate', 'zone_phone', 'huanxin']
        res = []
        for _ in range(cls.TEST_NUM):
            attrs = [cls.get_field_by_batchid([_, el]) for el in fields]
            user = User.create_by_phone(*attrs)
            zone_phone = attrs[-1]
            zone = zone_phone[:2]
            phone = zone_phone[2:]
            code = '8888'
            SmsCodeService.send_code(zone, phone)
            res.append(UserService.phone_login(zone, phone, code)[0])
        return res

    @classmethod
    def feed_num(cls, user_id):
        return 3