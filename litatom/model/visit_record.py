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


class VisitRecord(Document):
    meta = {
        'strict': False,
        'db_alias': 'relations',
        'shard_key': {'user_id': 'hashed'}
    }

    user_id = StringField(required=True, unique=True)
    target_user_id = StringField()
    visit_num = IntField(default=0)
    last_visited_time = DateTimeField(required=True, default=datetime.datetime.now)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_target_user_id(cls, user_id, page_num=0, num=20):
        start_num = page_num * num
        return cls.objects(target_user_id=user_id).order_by('-last_visited_time').skip(start_num).limit(num)

    @classmethod
    def get_by_user_id_target_user_id(cls, user_id, target_user_id):
        return cls.objects(user_id=user_id, target_user_id=user_id).first()

    @classmethod
    def add_visit(cls, user_id, target_user_id):
        obj = cls.get_by_user_id_target_user_id(user_id, target_user_id)
        if not obj:
            obj = cls(user_id=user_id, target_user_id=target_user_id)
        obj.visit_num += 1
        obj.last_visited_time = datetime.datetime.now()
        obj.save()


class DiffVisitRecord(Document):
    meta = {
        'strict': False,
        'db_alias': 'relations',
        'shard_key': {'visited_user_id': 'hashed'}
    }

    visited_user_id = StringField(required=True, unique=True)   # 被访问者的id
    recorded_visit_num = IntField(default=0)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def record_recorded(cls, visited_user_id):
        pass

