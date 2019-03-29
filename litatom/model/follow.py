# coding: utf-8
import datetime
import time
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)

class Follow(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    uid = StringField(required=True)
    followed = StringField(required=False)
    create_time = IntField(required=True)

    @classmethod
    def get_by_follow(cls, uid, followed):
        return cls.objects(uid=uid, followed=followed).first()


    @classmethod
    def in_follow(cls, uid, followed):
        obj = cls.get_by_follow(uid, followed)
        if obj:
            return True
        return False

    @classmethod
    def follow(cls, uid, followed):
        if not cls.get_by_follow(uid, followed):
            obj = cls(uid=uid, followed=followed)
            obj.create_time = int(time.time())
            obj.save()
            return True
        return False

    @classmethod
    def unfollow(cls, uid, followed):
        obj = cls.get_by_follow(uid, followed)
        if obj:
           obj.delete()
           obj.save()
           return True
        return False

    @classmethod
    def reverse(cls, uid, followed):
        '''
        返回最终是否是follow
        :param uid:
        :param followed:
        :return:
        '''
        obj = cls.get_by_follow(uid, followed)
        if not obj:
            obj = cls(uid=uid, followed=followed)
            obj.save()
            followed = True
        else:
            obj.delete()
            followed = False
        return followed

