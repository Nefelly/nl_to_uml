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


class UserModel(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    DEFAULT_SCORE = -1
    user_id = StringField(required=True)
    alert_num = IntField(required=True, default=0)
    match_times = IntField(default=0)
    total_match_inter = FloatField(default=0)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)
    # 确定用户的评论回复力
    total_comments = IntField(default=0)  # 用户总评论数
    total_comments_replies = FloatField(default=0)  # 用户评论总回复数
    block_num = IntField(default=0)  # 用户屏蔽的人数

    @classmethod
    def create(cls, user_id):
        # if cls.get_by_user_id(user_id):
        #     return True
        obj = cls(user_id=user_id)
        obj.save()
        return obj

    @cached_property
    def avr_match(self):
        if self.match_times == 0:
            return self.DEFAULT_SCORE
        return self.total_match_inter / self.match_times

    @cached_property
    def avr_comment_replies(self):
        if self.total_comments == 0:
            return 0
        return self.total_comments_replies / self.total_comments

    @classmethod
    def get_by_user_id(cls, user_id):
        cache_key = REDIS_USER_MODEL_CACHE.format(user_id=user_id)
        cache_obj = redis_client.get(cache_key)
        if cache_obj:
            return cPickle.loads(cache_obj)
        obj = cls.pure_get_by_user_id(user_id)
        redis_client.set(cache_key, cPickle.dumps(obj), USER_ACTIVE)
        return obj

    @classmethod
    def get_block_num_by_user_id(cls, user_id):
        user = cls.get_by_user_id(user_id)
        if user:
            return user.block_num
        return None

    @classmethod
    def pure_get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id).first()

    @classmethod
    def batch_get_by_user_ids(cls, user_ids):
        user_ids = [el for el in user_ids if el]
        keys = [REDIS_USER_MODEL_CACHE.format(user_id=_) for _ in user_ids]
        m = {}
        for uid, obj in zip(user_ids, redis_client.mget(keys)):
            if not obj:
                obj = cls.get_by_user_id(uid)
            else:
                obj = cPickle.loads(obj)
            m[uid] = obj
        return m

    @classmethod
    def batch_get_score(cls, user_ids):
        res = []
        m = cls.batch_get_by_user_ids(user_ids[:100])
        for _ in user_ids:
            obj = m.get(_)
            if obj:
                score = obj.avr_match
            else:
                score = cls.DEFAULT_SCORE
            res.append([_, score])
        return res

    @classmethod
    def _disable_cache(cls, user_id):
        redis_client.delete(REDIS_USER_MODEL_CACHE.format(user_id=user_id))

    def save(self, *args, **kwargs):
        if getattr(self, 'user_id', ''):
            self._disable_cache(str(self.user_id))
        super(UserModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if getattr(self, 'user_id', ''):
            self._disable_cache(str(self.user_id))
        super(UserModel, self).delete(*args, **kwargs)

    @classmethod
    def add_alert_num(cls, user_id):
        obj = cls.get_by_user_id(user_id)
        if not obj:
            obj = cls(user_id=user_id, alert_num=1)
        else:
            obj.alert_num += 1
        obj.save()

    @classmethod
    def inc_block_num(cls, user_id):
        """增加一个屏蔽者"""
        obj = cls.get_by_user_id(user_id)
        if not obj:
            obj = cls(user_id=user_id, block_num=1)
        else:
            obj.block_num += 1
        obj.save()

    @classmethod
    def dec_block_num(cls, user_id):
        """减少一个屏蔽者"""
        obj = cls.get_by_user_id(user_id)
        if not obj:
            return False
        else:
            if obj.block_num <= 0:
                return False
            else:
                obj.block_num -= 1
        obj.save()
        return True

    @classmethod
    def add_match_record(cls, user_id, inter_time_total, times_total=1):
        obj = cls.ensure_model(user_id)
        obj.total_match_inter += inter_time_total
        obj.match_times += times_total
        obj.save()
        return True

    @classmethod
    def add_comment_record(cls, user_id):
        obj = cls.ensure_model(user_id)
        obj.total_comments += 1
        obj.save()

    @classmethod
    def add_comment_replies_record(cls, user_id):
        obj = cls.ensure_model(user_id)
        obj.total_comments_replies += 1
        obj.save()

    @classmethod
    def ensure_model(cls, user_id):
        obj = cls.get_by_user_id(user_id)
        if not obj:
            obj = cls.create(user_id)
        return obj


class Uuids(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    uuid = StringField(required=True)
    loc = StringField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, uuid, loc=None):
        obj = cls.objects(uuid=uuid).first()
        if not obj:
            obj = cls(uuid=uuid, loc=loc)
            obj.save()
        return str(obj.id)
