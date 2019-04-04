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
            redis_client.delete(REDIS_ADMIN_USER.format(session=session))
        td = datetime.datetime.now() - datetime.datetime(1980, 1, 1)
        ss = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6
        rs = sys_rnd.randint(10 ** 8, 10 ** 8 * 9)
        session = 'session.%d%d' % (ss, rs)
        redis_client.set(REDIS_ADMIN_USER.format(session=session), self.user_name, TWO_WEEKS)
        self.session = session
        self.save()
        return self.session
