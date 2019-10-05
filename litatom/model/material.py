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
from ..const import (
    GENDERS
)

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

    @classmethod
    def get_avatars(cls):
        if getattr(cls, 'avatars', None):
            return cls.avatars
        cls.avatars = {}
        cls.avatar_m = {}
        for g in GENDERS:
            if not cls.avatars.get(g):
                cls.avatars[g] = []
            objs = cls.objects(gender=g)
            for obj in objs:
                fileid = obj.fileid
                cls.avatars[g].append(fileid)
                cls.avatar_m[fileid] = g
        return cls.avatars

    @classmethod
    def valid_avatar(cls, fileid):
        cls.get_avatars()
        return cls.avatar_m.get(fileid, None) is not None


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