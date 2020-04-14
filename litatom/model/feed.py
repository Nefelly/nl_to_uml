# coding: utf-8
import datetime
import time
import bson
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
    get_time_info
)
from ..const import (
    DEFAULT_QUERY_LIMIT,
    ONE_HOUR,
    ONE_MIN,
    NAN
)
from ..key import (
    REDIS_FEED_CACHE,
    REDIS_FEED_LIKE_CACHE
)
from ..redis import RedisClient

redis_client = RedisClient()['lit']


class Feed(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias',

    }

    user_id = StringField(required=True)
    like_num = IntField(required=True, default=0)
    comment_num = IntField(required=True, default=0)
    content = StringField()
    pics = ListField(default=[])
    audios = ListField(default=[])
    self_high = BooleanField(default=False)
    create_time = IntField(required=True, default=int(time.time()))

    @classmethod
    def feed_num(cls, user_id):
        return cls.objects(user_id=user_id).count()

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id)

    @classmethod
    def _disable_cache(cls, feed_id):
        redis_client.delete(REDIS_FEED_CACHE.format(feed_id=feed_id))

    def save(self, *args, **kwargs):
        if getattr(self, 'id', ''):
            self._disable_cache(str(self.id))
        super(Feed, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if getattr(self, 'id', ''):
            self._disable_cache(str(self.id))
        super(Feed, self).delete(*args, **kwargs)

    @property
    def is_hq(self):
        return self.like_num >= 5 or self.comment_num >= 5 or (
                    len(self.audios) > 0 and self.like_num + self.comment_num > 2)

    def get_info(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'like_num': self.like_num,
            'comment_num': self.comment_num,
            'pics': self.pics if self.pics else [],
            'audios': self.audios if self.audios else [],
            'content': self.content,
            'create_time': get_time_info(self.create_time)
        }

    @classmethod
    def last_feed_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id).order_by("-create_time").first()
    
    def is_same(self, content, pics, audios):
        if not pics:
            pics = []
        if not audios:
            audios = []
        if not self.content:
            self.content = None
        if not content:
            content = None
        return self.pics == pics and self.content == content and self.audios == audios
    
    @classmethod
    def create_feed(cls, user_id, content, pics, audios):
        last = cls.last_feed_by_user_id(user_id)
        if last and last.is_same(content, pics, audios):
            return last
        obj = cls()
        obj.user_id = user_id
        obj.content = content
        obj.pics = pics
        obj.audios = audios
        obj.create_time = int(time.time())
        obj.save()
        return obj

    @classmethod
    def chg_like_num(cls, feed_id, num=1):
        feed = cls.get_by_id(feed_id)
        feed.like_num += num
        if feed.like_num < 0:
            feed.like_num = 0
        feed.save()

    @classmethod
    def cls_chg_comment_num(cls, feed_id, num=1):
        feed = cls.get_by_id(feed_id)
        feed.comment_num += num
        if feed.comment_num < 0:
            feed.comment_num = 0
        feed.save()

    def chg_comment_num(self, num=1):
        self.comment_num += num
        if self.comment_num < 0:
            self.comment_num = 0
        self.save()

    def chg_feed_num(self, num=1):
        self.like_num += num
        if self.like_num < 0:
            self.like_num = 0
        self.save()

    @classmethod
    def get_by_id(cls, feed_id):
        cache_key = REDIS_FEED_CACHE.format(feed_id=feed_id)
        cache_obj = redis_client.get(cache_key)
        if cache_obj:
            # redis_client.incr('feed_cache_hit_cnt')
            return cPickle.loads(cache_obj)
        if not bson.ObjectId.is_valid(feed_id):
            return None
        obj = cls.objects(id=feed_id).first()
        # redis_client.incr('feed_cache_miss_cnt')
        redis_client.set(cache_key, cPickle.dumps(obj), ex=ONE_HOUR)
        return obj

    @classmethod
    def get_by_create_time(cls, from_time, to_time):
        return cls.objects(create_time__gte=from_time, create_time__lte=to_time)


class FollowingFeed(Document):
    meta = {
        'strict': False,
        'db_alias': 'relations',
        'shard_key': {'user_id': 'hashed'}
    }
    user_id = StringField(required=True)
    followed_user_id = StringField(required=True)
    feed_id = StringField(required=True)
    feed_create_time = IntField(required=True)
    create_time = IntField(required=True)

    @classmethod
    def get_by_user_id_feed_id(cls, user_id, feed_id):
        return cls.objects(user_id=user_id, feed_id=feed_id).first()

    @classmethod
    def add_feed(cls, user_id, feed):
        if not feed:
            return True
        feed_id = str(feed.id)
        # obj = cls.get_by_user_id_feed_id(user_id, feed_id)
        # if obj:
        #     return True
        obj = cls()
        obj.user_id = user_id
        obj.followed_user_id = feed.user_id
        obj.feed_id = feed_id
        obj.feed_create_time = feed.create_time
        obj.create_time = int(time.time())
        obj.save()
        return True

    @classmethod
    def delete_feed(cls, user_id, feed):
        if not feed:
            return True
        feed_id = str(feed.id)
        obj = cls.get_by_user_id_feed_id(user_id, feed_id)
        if obj:
            obj.delete()
            obj.save()
        return True


class FeedLike(Document):
    LIKE_NUM_THRESHOLD = 500
    PROTECT = 5
    CACHED_TIME = 50 * ONE_MIN
    feed_id = StringField(required=True)
    uid = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_ids(cls, uid, feed_id):
        return cls.objects(uid=uid, feed_id=feed_id).first()

    @classmethod
    def get_redis_key(cls, feed_id):
        return REDIS_FEED_LIKE_CACHE.format(feed_id=feed_id)

    @classmethod
    def ensure_cache(cls, feed_id):
        key = cls.get_redis_key(feed_id)
        if not redis_client.exists(key):
            uids = [e.uid for e in cls.objects(feed_id=feed_id)]
            if uids:
                redis_client.sadd(key, *uids)
                redis_client.expire(key, cls.CACHED_TIME)
            # 在没有值的键上补充一个占位符，避免redis优化自动删除该键导致重复建立
            else:
                redis_client.sadd(key, NAN)
                redis_client.expire(key, cls.CACHED_TIME)

    @classmethod
    def in_like(cls, uid, feed_id, feed_like_num):
        """
        根据uid,feed_id，判断uid对feed_id是否like
        1. 如果feed_like_num小于等于LIKE_NUM_THRESHOLD-PROTECT，必须缓存进redis
        2. 如果feed_like_num已经大于等于LIKE_NUM_THRESHOLD,必须清除缓存
        3. 如果feed_like_num介于(LIKE_NUM_THRESHOLD-PROTECT,LIKE_NUM_THRESHOLD)，暂不清除缓存，但是用db检索数据
        """
        key = cls.get_redis_key(feed_id)
        if feed_like_num > cls.LIKE_NUM_THRESHOLD - cls.PROTECT:  # PROTECT 用来保护缓存不会因为like num 一上一下不断刷缓存
            if feed_like_num >= cls.LIKE_NUM_THRESHOLD:
                redis_client.delete(key)
            obj = cls.get_by_ids(uid, feed_id)
            return True if obj else False
        cls.ensure_cache(feed_id)
        return redis_client.sismember(key, uid)

    @classmethod
    def del_by_feedid(cls, feed_id):
        cls.objects(feed_id=feed_id).delete()

    # @classmethod
    # def like(cls, uid, feed_id):
    #     if not cls.get_by_ids(uid, feed_id):
    #         obj = cls(uid=uid, feed_id=feed_id)
    #         obj.save()
    #     return True
    #
    # @classmethod
    # def unlike(cls, uid, feed_id):
    #     obj = cls.get_by_ids(uid, feed_id)
    #     if obj:
    #         obj.delete()
    #         obj.save()
    #         return True
    #     return False

    # def save(self, *args, **kwargs):
    #     if getattr(self, 'user_id', ''):
    #         self._disable_cache(str(self.user_id))
    #     super(FeedLike, self).save(*args, **kwargs)
    #
    # def delete(self, *args, **kwargs):
    #     if getattr(self, 'user_id', ''):
    #         self._disable_cache(str(self.user_id))
    #     super(FeedLike, self).delete(*args, **kwargs)

    @classmethod
    def reverse(cls, uid, feed_id, feed_like_num):
        '''
        返回最终是否是like
        :param feed_like_num:
        :param uid:
        :param feed_id:
        :return:
        '''
        obj = cls.get_by_ids(uid, feed_id)
        if not obj:
            obj = cls(uid=uid, feed_id=feed_id)
            obj.save()
            like_now = True
        else:
            obj.delete()
            like_now = False
        # 1. 如果feed_like_num >= LIKE_NUM_THRESHOLD，则无论结果如何，不必将数据缓存
        # 2. 如果feed_like_num属于[LIKE_NUM_THRESHOLD-PROTECT,LIKE_NUM_THRESHOLD)，
        #       在该feed已经被缓存的情况下，如果新增like则缓存该项，如果去掉like则移除缓存该项
        # 3. 如果feed_like_num < LIKE_NUM_THRESHOLD - PROTECT,必须确保有缓存，然后更新缓存
        if cls.LIKE_NUM_THRESHOLD > feed_like_num:
            key = cls.get_redis_key(feed_id)
            if cls.LIKE_NUM_THRESHOLD - cls.PROTECT <= feed_like_num:
                if redis_client.exists(key):
                    if like_now:
                        redis_client.sadd(key, uid)
                    else:
                        redis_client.srem(key, uid)
            else:
                cls.ensure_cache(feed_id)
                if like_now:
                    redis_client.sadd(key, uid)
                else:
                    redis_client.srem(key, uid)
        return like_now


class FeedComment(Document):
    feed_id = StringField(required=True)
    comment_id = StringField()  # father comment_id
    user_id = StringField(required=True)
    content = StringField(required=True)
    content_user_id = StringField()
    create_time = IntField(required=True)

    @classmethod
    def get_by_id(cls, comment_id):
        if not bson.ObjectId.is_valid(comment_id):
            return None
        return cls.objects(id=comment_id).first()

    @classmethod
    def get_by_feed_id(cls, feed_id):
        return cls.objects(feed_id=feed_id).order_by('-create_time').limit(DEFAULT_QUERY_LIMIT)
