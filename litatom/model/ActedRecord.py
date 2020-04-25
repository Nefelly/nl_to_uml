# coding: utf-8
import datetime
import cPickle
from hendrix.conf import setting
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
    FloatField
)
from ..redis import RedisClient
from ..const import (
    USER_ACTIVE
)
from ..util import (
    cached_property
)
from ..key import (
    REDIS_USER_MODEL_CACHE
)

redis_client = RedisClient()['lit']


class ActedRecord(Document):
    meta = {
        'strict': False,
        'db_alias': 'relations',
        'shard_key': {'uid': 'hashed'}
    }
    COMUNITY_ACT = 'community_rule'
    user_id = StringField(required=True)
    content = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, user_id, content):
        if cls.get_by_user_id_content(user_id, content):
            return True
        obj = cls(user_id=user_id, content=content)
        obj.save()
        return obj

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id)

    @classmethod
    def get_by_user_id_content(cls, user_id, content):
        return cls.objects(user_id=user_id, content=content).first()
