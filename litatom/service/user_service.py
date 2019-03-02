import random

from ..redis import RedisClient
from ..util import validate_phone_number

from ..model import User
from ..service import (
    SmsCodeService
)

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

class UserService(object):

    @classmethod
    def phone_login(cls, zone, phone, code):
        msg, status = SmsCodeService.verify_code(zone, phone, code)
        if not status:
            return msg, status
        zone_phone = validate_phone_number(zone + phone)
        if not zone_phone:
            return cls.ERR_WORONG_TELEPHONE, False
        user = User.get_by_phone(zone_phone)
        if not user:
            user = User()
            user.phone = zone_phone
            user.save()
        user.generate_new_session()
        user._set_session_cache(str(user.id))
        return {
            'session': user.session,
            'finished_info': user.finished_info
        }, True
