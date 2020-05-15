# coding: utf-8
import datetime
import random
import time
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from ..util import (
    date_to_int_time
)
from .. key import (
    REDIS_NEW_VISIT_NUM
)
from ..const import (
    ONE_DAY
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

    user_id = StringField(required=True)
    target_user_id = StringField()
    visit_num = IntField(default=0)
    last_visited_time = IntField(required=True, default=int(time.time()))
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_target_user_id(cls, target_user_id, page_num=0, num=20):
        start_num = page_num * num
        return cls.objects(target_user_id=target_user_id).order_by('-last_visited_time').skip(start_num).limit(num)

    @classmethod
    def get_by_user_id_target_user_id(cls, user_id, target_user_id):
        return cls.objects(user_id=user_id, target_user_id=target_user_id).first()

    @classmethod
    def add_visit(cls, user_id, target_user_id):
        obj = cls.get_by_user_id_target_user_id(user_id, target_user_id)
        if not obj:
            obj = cls(user_id=user_id, target_user_id=target_user_id)
        obj.visit_num += 1
        obj.last_visited_time = int(time.time())
        obj.save()

    def to_json(self):
        return {
            'last_visit_time': self.last_visited_time,
            'user_id': self.user_id,
            'visit_num': self.visit_num
        }


class NewVisit(Document):
    meta = {
        'strict': False,
        'db_alias': 'relations',
        'shard_key': {'visited_user_id': 'hashed'}
    }

    visited_user_id = StringField(required=True, unique=True)   # 被访问者的id
    new_visit_num = IntField(default=0)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)
    VISITED_CACHE_TIME = ONE_DAY

    @classmethod
    def new_visited_cache_key(cls, user_id):
        return REDIS_NEW_VISIT_NUM.format(user_id=user_id)

    @classmethod
    def incr_visited(cls, visited_user_id):
        obj = cls.get_by_visited_user_id(visited_user_id)
        if not obj:
            obj = cls(visited_user_id=visited_user_id)
        obj.new_visit_num += 1
        obj.save()
        cls.disable_cache(visited_user_id)

    @classmethod
    def new_visit_num(cls, visited_user_id):
        num = redis_client.get(cls.new_visited_cache_key(visited_user_id))
        if num is None:
            obj = cls.get_by_visited_user_id(visited_user_id)
            if obj:
                num = obj.new_visit_num
            else:
                num = 0
            redis_client.set(cls.new_visited_cache_key(visited_user_id), num, cls.VISITED_CACHE_TIME)
        else:
            num = int(num)
        return num


    @classmethod
    def disable_cache(cls, visited_user_id):
        redis_client.delete(cls.new_visited_cache_key(visited_user_id))

    @classmethod
    def record_has_viewed(cls, visited_user_id):
        obj = cls.get_by_visited_user_id(visited_user_id)
        if obj:
            obj.new_visit_num = 0
            obj.save()
        redis_client.set(cls.new_visited_cache_key(visited_user_id), 0, cls.VISITED_CACHE_TIME)

    @classmethod
    def get_by_visited_user_id(cls, visited_user_id):
        return cls.objects(visited_user_id=visited_user_id).first()