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
    REDIS_EXP_BUCKET_VALUE
)
from ..const import (
    TWO_WEEKS
)
from ..redis import RedisClient

sys_rnd = random.SystemRandom()
volatile_redis = RedisClient()['volatile']


class ExpBucket(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    BUCKET_KEY_TTL = TWO_WEEKS
    NOSET = 'noset'
    DEFAULT = 'default'


    exp_name = StringField(required=True)
    bucket_id = IntField(required=True)
    value = StringField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def _get_by_exp_name_bucket(cls, exp_name, bucket_id):
        return cls.objects(exp_name=exp_name, bucket_id=bucket_id).first()

    @classmethod
    def get_by_exp_name_bucket_id(cls, exp_name, bucket_id):
        key = cls._bucket_key(exp_name, bucket_id)
        res = volatile_redis.get(key)
        if res:
            return res
        obj = cls._get_by_exp_name_bucket(exp_name, bucket_id)
        res = cls.NOSET if not obj or not obj.value else obj.value
        volatile_redis.set(key, res, cls.BUCKET_KEY_TTL)
        return res

    @classmethod
    def _bucket_key(cls, exp_name, bucket):
        return REDIS_EXP_BUCKET_VALUE.format(exp_bucket='%s_%2d' % (exp_name, bucket))

    @classmethod
    def disable_cache(cls, exp_name, bucket):
        volatile_redis.delete(cls._bucket_key(exp_name, bucket))

    def save(self, *args, **kwargs):
        exp_name = getattr(self, 'exp_name', '')
        bucket_id = getattr(self, 'bucket_id', -1)
        self.disable_cache(exp_name, bucket_id)
        return super(ExpBucket, self).save(*args, **kwargs)

    @classmethod
    def create(cls, exp_name, bucket_id, value):
        obj = cls._get_by_exp_name_bucket(exp_name, bucket_id)
        if not obj:
            obj = cls()
        obj.exp_name = exp_name
        obj.bucket_id = bucket_id
        obj.value = value
        obj.save()
        return obj

    @classmethod
    def get_values(cls, exp_name):
        values = cls.objects(exp_name=exp_name).distinct('value')
        return list(set(values + [cls.NOSET, cls.DEFAULT]))

    @classmethod
    def load_buckets(cls, exp_name):
        '''
        :param exp_name:
        :return: {value: [bucket_num], value:[bucket_num]}
        '''
        res = {}
        for _ in cls.objects(exp_name=exp_name):
            value = _.value
            if not res.get(value):
                res[value] = [_.bucket_id]
            else:
                res[value].append(_.bucket_id)
        return res


class Experiments(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    BUCKET_KEY_TTL = TWO_WEEKS
    NOSET = 'noset'
    DEFAULT = 'default'

    exp_name = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)