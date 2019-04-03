# coding: utf-8
import random
import time
import datetime

from ..redis import RedisClient

from ..key import (
    REDIS_USER_INFO_FINISHED,
    REDIS_KEY_SESSION_USER,
    REDIS_UID_GENDER,
    REDIS_ONLINE
)
from ..const import (
    TWO_WEEKS
)

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

class AdminService(object):
    UID_PWDS = {
        'joey': 'hypercycle'
    }

    @classmethod
    def gen_session(cls):
        td = datetime.datetime.now() - datetime.datetime(1980, 1, 1)
        ss = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6
        rs = sys_rnd.randint(10 ** 8, 10 ** 8 * 9)
        return 'session.%d%d' % (ss, rs)

    @classmethod
    def login(cls, user_name, pwd):
        """
        登录的动作
        :param user:
        :return:
        """
        if cls.get(user_name, '') == pwd:
            session = cls.gen_session()
            key = REDIS_KEY_SESSION_USER.format(session=session)
            redis_client.set(key, user_name, ex=TWO_WEEKS)
            return {
                'session': session
            }, True
        return None, False

    @classmethod
    def is_admin(cls, username):
        if cls.UID_PWDS.get(username, ''):
            return True
        return False
