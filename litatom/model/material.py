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


class Wording(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    word_type = StringField(required=True)
    content = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, nickname, gender):
        obj = cls(nickname=nickname, gender=gender)
        obj.save()

