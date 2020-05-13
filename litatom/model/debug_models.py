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
    ONE_DAY
)
from ..model import (
    User
)
from ..redis import RedisClient

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']


class UserLogs(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    user_id = StringField(required=True, unique=True)
    file_id = StringField(required=True, unique=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def add_user_log(cls, user_id, file_id):
        obj = cls(user_id=user_id, file_id=file_id)
        obj.save()

    @classmethod
    def get_latest_file_id(cls, user_id):
        obj = cls.objects(user_id=user_id).order_by('-create_time').first()
        if not obj:
            return None
        return obj.file_id
