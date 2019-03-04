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

class Follow(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    uid = StringField(required=True)
    followed = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_follow(cls, uid, followed):
        return cls.objects(uid=uid, followed=followed).first()

    @classmethod
    def follow(cls, uid, followed):
        if not cls.get_by_follow(uid, followed):
            obj = cls(uid=uid, followed=followed)
            obj.save()
        return True

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

