# coding: utf-8
import random
import time
import datetime
from ..model import AdminUser

from ..redis import RedisClient

from ..key import (
    REDIS_USER_INFO_FINISHED,
    REDIS_ADMIN_USER
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
    def get_user_name_by_session(cls, session):
        return redis_client.get(REDIS_ADMIN_USER.format(session=session))

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
        admin_user = AdminUser.get_by_user_name(user_name)
        if admin_user and admin_user.pwd == pwd:
            session = admin_user.gen_session()
            return {
                'session': session
            }, True
        return None, False

    @classmethod
    def create(cls, user_name, pwd):
        obj = AdminUser()
        obj.user_name = user_name
        obj.pwd = pwd
        obj.create_time = datetime.datetime.now()
        obj.save()
