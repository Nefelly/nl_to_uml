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

class Blocked(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    uid = StringField(required=True)
    blocked = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_block(cls, uid, blocked):
        return cls.objects(uid=uid, blocked=blocked).first()

    @classmethod
    def block(cls, uid, blocked):
        if not cls.get_by_block(uid, blocked):
            obj = cls(uid=uid, blocked=blocked)
            obj.save()
        return True

    @classmethod
    def unblock(cls, uid, blocked):
        obj = cls.get_by_block(uid, blocked)
        if obj:
            obj.delete()
            obj.save()
            return True
        return False

    @classmethod
    def reverse(cls, uid, blocked):
        '''
        返回最终是否是block
        :param uid:
        :param blocked:
        :return:
        '''
        obj = cls.get_by_block(uid, blocked)
        if not obj:
            obj = cls(uid=uid, blocked=blocked)
            obj.save()
            blocked = True
        else:
            obj.delete()
            blocked = False
        return blocked
