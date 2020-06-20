# coding: utf-8
import datetime
import random
import cPickle
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
    REDIS_TAG_CACHE,
    REDIS_USER_TAG_CACHE
)
from ..const import (
    ONE_DAY
)
from ..redis import RedisClient

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']


class Tag(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    name = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, name):
        obj = cls(name=name)
        obj.save()

    @classmethod
    def _disable_cache(cls):
        redis_client.delete(REDIS_TAG_CACHE)

    def save(self, *args, **kwargs):
        super(Tag, self).save(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache()

    def delete(self, *args, **kwargs):
        super(Tag, self).delete(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache()

    def to_json(self):
        return {
            'id': str(self.id),
            'name': self.name
        }

    @classmethod
    def get_tags(cls):
        cache_obj = redis_client.get(REDIS_TAG_CACHE)
        if cache_obj:
            return cPickle.loads(cache_obj)
        tags = []
        for tag in cls.objects():
            tags.append(tag.to_json())
        redis_client.set(REDIS_TAG_CACHE, cPickle.dumps(tags))
        return tags


class UserTag(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    user_id = StringField(required=True)
    tag_id = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id)

    @classmethod
    def get_by_ids(cls, user_id, tag_id):
        return cls.objects(user_id=user_id, tag_id=tag_id)

    @classmethod
    def get_cached_key(cls, user_id):
        return REDIS_USER_TAG_CACHE.format(user_id=user_id)

    @classmethod
    def _disable_cache(cls, user_id):
        redis_client.delete(cls.get_cached_key(user_id))

    def save(self, *args, **kwargs):
        if getattr(self, 'user_id', ''):
            self._disable_cache(str(self.user_id))
        super(UserTag, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        print 'get in herrrr'
        if getattr(self, 'user_id', ''):
            self._disable_cache(str(self.user_id))
        super(UserTag, self).delete(*args, **kwargs)

    @classmethod
    def create(cls, user_id, tag_id):
        if cls.get_by_ids(user_id, tag_id):
            return True
        obj = cls(user_id=user_id, tag_id=tag_id)
        obj.save()
        return True
