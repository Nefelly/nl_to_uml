import random

from ..redis import RedisClient
from ..util import validate_phone_number

from ..key import (
    REDIS_KEY_SMS_CODE
)
from ..const import TEN_MINS

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

class SmsCodeService(object):
    """
    """
    LIVE_TIME = TEN_MINS
    CODE_LEN = 4
    CODE_CHARS = [str(i) for i in range(10)]

    @classmethod
    def gen_code(cls):
        res = ''
        return '8888'
        for _ in cls.CODE_LEN:
            res += sys_rnd.choice(cls.CODE_CHARS)
        return res

    @classmethod
    def send_code(cls, zone, phone):
        zone_phone = zone + phone
        zone_phone = validate_phone_number(zone_phone)
        if not zone_phone:
            return u'wrong telephone number', False
        code = cls.gen_code()
        # TODO: send code to user

        key = REDIS_KEY_SMS_CODE.format(phone=zone_phone)
        redis_client.set(key, code, ex=TEN_MINS)
        return '', True

    @classmethod
    def verify_code(cls, zone, phone, code):
        zone_phone = zone + phone
        zone_phone = validate_phone_number(zone_phone)
        if not zone_phone:
            return u'wrong telephone number', False
        key = REDIS_KEY_SMS_CODE.format(phone=zone_phone)
        cached_code = redis_client.get(key)
        if not cached_code or cached_code != code:
            return u'wrong code', False
        return '', True
