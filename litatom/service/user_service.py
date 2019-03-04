import random

from ..redis import RedisClient
from ..util import validate_phone_number
from ..const import (
    INT_BOY,
    INT_GIRL
)

from ..model import User
from ..service import (
    SmsCodeService,
    FeedService
)

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

class UserService(object):

    @classmethod
    def login_job(cls, user):
        """
        登录的动作
        :param user:
        :return:
        """
        user.generate_new_session()
        user._set_session_cache(str(user.id))
        if not user.logined:
            user.logined = True
            user.save()

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
        cls.login_job(user)

        basic_info = user.basic_info()
        login_info = user.get_login_info()
        return basic_info.update(login_info), True

    @classmethod
    def get_bio(cls, user):
        if user.bio:
            return user.bio
        feed_num = FeedService.feed_num(str(user.id))
        he_or_she = 'He' if user.gender == INT_BOY else 'She'
        if feed_num > 3:
            return u'%s is mysterious~' % he_or_she
        return u'%s loves to share' % he_or_she

    @classmethod
    def verify_nickname(cls, nickname):
        if User.get_by_nickname(nickname):
            return True
        return False

    @classmethod
    def get_avatars(cls):
        return

