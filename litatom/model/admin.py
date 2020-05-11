# coding: utf-8
import datetime
import random
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from .. key import (
    REDIS_ADMIN_USER
)
from ..const import (
    TWO_WEEKS
)
from ..redis import RedisClient

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

class AdminUser(Document):
    '''
    '5e357b07f142533fff0049c2',  # 绿杨
    '5cb7536f3fff221c27f959b6',  # 第二个绿杨
    '5e651b6dad85ef6fb4664815',  # Norman,ID
    '5da849e33fff225cb55d1e73',  # 王贤思,VN
    '5e1d822b3fff223633a2ba2d',  # 乐乐,VN
    '5cebd0763fff225dc7f2bba5',  # Alice 麦明芳,ID
    '5e70414578e8443ea1ac48d2',  # 54, TH
    '''
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    user_name = StringField(required=True, unique=True)
    pwd = StringField(required=True)
    session = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_user_name(cls, user_name):
        return cls.objects(user_name=user_name).first()


    def gen_session(self):
        if self.session:
            redis_client.delete(REDIS_ADMIN_USER.format(session=self.session))
        td = datetime.datetime.now() - datetime.datetime(1980, 1, 1)
        ss = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6
        rs = sys_rnd.randint(10 ** 8, 10 ** 8 * 9)
        session = 'session.%d%d' % (ss, rs)
        redis_client.set(REDIS_ADMIN_USER.format(session=session), self.user_name, ex=TWO_WEEKS)
        self.session = session
        self.save()
        return self.session


class AppAdmin(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    user_id = StringField(required=True, unique=True)
    nickname = StringField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def is_admin(cls, user_id):
        return cls.objects(user_id=user_id).count() > 0
