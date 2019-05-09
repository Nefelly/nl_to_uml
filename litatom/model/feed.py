# coding: utf-8
import datetime
import time
import bson
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
    DEFAULT_QUERY_LIMIT
)

class Feed(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    user_id = StringField(required=True)
    like_num = IntField(required=True, default=0)
    comment_num = IntField(required=True, default=0)
    content = StringField()
    pics = ListField(default=[])
    create_time = IntField(required=True)

    @classmethod
    def feed_num(cls, user_id):
        return cls.objects(user_id=user_id).count()

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id)

    @property
    def is_hq(self):
        return self.like_num >= 2 or self.comment_num >= 2

    def get_info(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'like_num': self.like_num,
            'comment_num': self.comment_num,
            'pics': self.pics if self.pics else [],
            'content': self.content,
            'create_time': get_time_info(self.create_time)
        }

    @classmethod
    def last_feed_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id).order_by("-create_time").first()

    @classmethod
    def create_feed(cls, user_id, content, pics):
        last = cls.last_feed_by_user_id(user_id)
        if last and last.pics == pics and last.content == content:
            return last
        obj = cls()
        obj.user_id = user_id
        obj.content = content
        obj.pics = pics
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
        if not bson.ObjectId.is_valid(feed_id):
            return None
        return cls.objects(id=feed_id).first()

class FollowingFeed(Document):
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
        obj = cls.get_by_user_id_feed_id(user_id, feed_id)
        if obj:
            return True
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
    feed_id = StringField(required=True)
    uid = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_ids(cls, uid, feed_id):
        return cls.objects(uid=uid, feed_id=feed_id).first()

    @classmethod
    def like(cls, uid, feed_id):
        if not cls.get_by_ids(uid, feed_id):
            obj = cls(uid=uid, feed_id=feed_id)
            obj.save()
        return True

    @classmethod
    def unlike(cls, uid, feed_id):
        obj = cls.get_by_ids(uid, feed_id)
        if obj:
            obj.delete()
            obj.save()
            return True
        return False

    @classmethod
    def reverse(cls, uid, feed_id):
        '''
        返回最终是否是like
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