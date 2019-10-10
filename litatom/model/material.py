# coding: utf-8
import datetime
import cPickle
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from ..redis import RedisClient
from ..const import (
    GENDERS
)
from ..key import (
    REDIS_AVATAR_CACHE
)
redis_client = RedisClient()['lit']

class Avatar(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    fileid = StringField(required=True)
    gender = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, fileid, gender):
        obj = cls(fileid=fileid, gender=gender)
        obj.save()
        cls._disable_cache()

    @classmethod
    def _disable_cache(cls):
        redis_client.delete(REDIS_AVATAR_CACHE)

    def save(self, *args, **kwargs):
        super(Avatar, self).save(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache()

    def delete(self, *args, **kwargs):
        super(Avatar, self).delete(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache()

    @classmethod
    def get_avatars(cls):
        cache_obj = redis_client.get(REDIS_AVATAR_CACHE)
        if cache_obj:
            return cPickle.loads(cache_obj)
        avatars = {}
        for g in GENDERS:
            if not avatars.get(g):
                avatars[g] = []
            objs = cls.objects(gender=g)
            for obj in objs:
                fileid = obj.fileid
                avatars[g].append(fileid)
        redis_client.set(REDIS_AVATAR_CACHE, cPickle.dumps(avatars))
        return avatars

    @classmethod
    def valid_avatar(cls, fileid):
        avatars = cls.get_avatars()
        for _ in GENDERS:
            if fileid in avatars[_]:
                return True
        return False

class Wording(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    word_type = StringField(required=True)
    content = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, content, word_type):
        obj = cls.objects(word_type=word_type).first()
        if obj:
            return 
        obj = cls(content=content, word_type=word_type)
        obj.save()
    
    @classmethod
    def get_word_type(cls, word_type):
        if getattr(cls, 'word_types', None):
            return cls.word_types.get(word_type, '')
        cls.word_types = {}
        for obj in cls.objects():
            cls.word_types[obj.word_type] = obj.content
        return cls.word_types.get(word_type, '')