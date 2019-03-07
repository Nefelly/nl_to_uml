# coding: utf-8
import datetime
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

class Feed(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    user_id = StringField(required=True)
    like_num = IntField(required=True, default=0)
    comment_num = IntField(required=True, default=0)
    pics = ListField(required=True, default=[])
    create_time = DateTimeField(required=True, default=datetime.datetime.now)
    
    def get_info(self):
        return {
            'user_id': self.user_id,
            'like_num': self.like_num,
            'comment_num': self.comment_num,
            'pics': self.pics if self.pics else [],
            'create_time': date_to_int_time(self.create_time)

        }

    @classmethod
    def create_feed(cls, user_id, words, pics):
        obj = cls()
        cls.user_id = user_id
        cls.words = words
        cls.pics = pics
        obj.save()
        return obj

    @classmethod
    def get_by_id(cls, feed_id):
        return cls.objects().first()

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
            feed_id = True
        else:
            obj.delete()
            feed_id = False
        return feed_id


class FeedComment(Document):
    feed_id = StringField(required=True)
    comment_id = StringField(required=True)
    uid = StringField(required=True)
    content = StringField(required=True)
    time = DateTimeField(required=True, default=datetime.datetime.now)