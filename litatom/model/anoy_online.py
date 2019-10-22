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

class AnoyOnline(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    gender = StringField(required=True, unique=True)
    region = StringField(required=True)
    match_type = StringField(required=False)
    stat_time = IntField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_user_name(cls, user_name):
        return cls.objects(user_name=user_name).first()

    @classmethod
    def create(cls, gender, region, match_type, stat_time):
        obj = cls()
        obj.gender = gender
        obj.region = region
        obj.match_type = match_type
        obj.stat_time = stat_time
        obj.save()
