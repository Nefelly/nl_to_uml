# coding: utf-8
import datetime
import hashlib
import logging
import json
import random
sys_rng = random.SystemRandom()
import urlparse

import re
import bson
from hendrix.conf import setting
from hendrix.util import Enum
from mongoengine import (
    NULLIFY,
    BooleanField,
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    ObjectIdField,
    ReferenceField,
    StringField,
    QuerySet,
    Q,
    ValidationError,
)

from ..util import (
    format_standard_time,
    unix_ts_local,
    passwdhash,
)

logger = logging.getLogger(__name__)
requests = None


class User(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }


    nickname = StringField()
    gender = IntField()

    @classmethod
    def create(cls, nickname, gender):
        user = User(nickname=nickname, gender=gender)
        user.save()
        return user

    @classmethod
    def get_by_nickname(cls, nickname):
        return cls.objects(nickname=nickname).first()
