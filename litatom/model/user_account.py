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
    FloatField
)
from ..const import (
    USER_ACTIVE
)
from ..key import (
    REDIS_USER_ACCOUNT_CACHE
)
from ..redis import RedisClient

redis_client = RedisClient()['lit']


class UserAccount(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    user_id = StringField(required=True)
    diamonds = IntField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id).first()

    @classmethod
    def get_by_user_id(cls, user_id):
        cache_key = REDIS_USER_ACCOUNT_CACHE.format(user_id=user_id)
        cache_obj = redis_client.get(cache_key)
        if cache_obj:
            # redis_client.incr('account_cache_hit_cnt')
            return cPickle.loads(cache_obj)
        obj = cls.objects(user_id=user_id).first()
        # redis_client.incr('account_cache_miss_cnt')
        redis_client.set(cache_key, cPickle.dumps(obj), USER_ACTIVE)
        return obj

    @classmethod
    def _disable_cache(cls, user_id):
        redis_client.delete(REDIS_USER_ACCOUNT_CACHE.format(user_id=user_id))

    def save(self, *args, **kwargs):
        if getattr(self, 'user_id', ''):
            self._disable_cache(str(self.user_id))
        super(UserAccount, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if getattr(self, 'user_id', ''):
            self._disable_cache(str(self.user_id))
        super(UserAccount, self).delete(*args, **kwargs)

    @classmethod
    def create_account(cls, user_id, diamonds=0):
        if cls.get_by_user_id(user_id):
            return True
        obj = cls(user_id=user_id, diamonds=diamonds)
        obj.save()
        return True

    @classmethod
    def ensure_account(cls, user_id, diamonds=0):
        obj = cls.get_by_user_id(user_id)
        if not obj:
            cls.create_account(user_id, diamonds)
        else:
            obj.diamonds = diamonds
            obj.save()
        return True


class AccountFlowRecord(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    DEPOSIT = 'deposit'
    CONSUME = 'consume'

    user_id = StringField(required=True)
    action = StringField(required=True)
    money = FloatField(required=True, default=0)
    diamonds = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)
