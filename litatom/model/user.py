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
from ..key import (
    REDIS_KEY_SESSION_USER
)
from ..const import TWO_WEEKS
from ..redis import RedisClient
from ..util import (
    format_standard_time,
    unix_ts_local,
    passwdhash,
)

logger = logging.getLogger(__name__)
requests = None
redis_client = RedisClient()['lit']

class UserSessionMixin(object):
    SESSION_ID_PATTERN = 'session.{id}'

    @property
    def session_id(self):
        if not self.session:
            return ''
        return self.SESSION_ID_PATTERN.format(id=self.session)

    sessionid = session_id  # compat

    def _build_session_string(self):
        td = datetime.datetime.now() - datetime.datetime(1980, 1, 1)
        ss = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6
        rs = sys_rng.randint(10 ** 8, 10 ** 8 * 9)
        if self.finished_info:
            return '%d%d' % (ss, rs)
        return 'N%d%d' % (ss, rs)

    def _purge_session_cache(self):
        key = REDIS_KEY_SESSION_USER.format(session=self.session)
        redis_client.delete(key)

    def _set_session_cache(self, user_id):
        key = REDIS_KEY_SESSION_USER.format(session=self.session)
        redis_client.set(key, user_id, ex=TWO_WEEKS)

    def clear_session(self):
        if not self.session:
            return
        self._purge_session_cache()
        self.session = None
        self.save()

    def generate_new_session(self):
        self.clear_session()
        self.session = self._build_session_string()
        self.sessionCreateTime = datetime.datetime.now()
        self.save()
        return self.session

    new_session = generate_new_session

class User(Document, UserSessionMixin):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }


    nickname = StringField()
    avatar = StringField()
    gender = IntField()
    birthdate = StringField()
    session = StringField()
    sessionCreateTime = DateTimeField()
    isFirstLogin = BooleanField()
    bio = StringField()
    phone = StringField()
    judge = ListField(default=[0, 0, 0])   # nasty, boring, like

    @classmethod
    def create(cls, nickname, gender):
        user = User(nickname=nickname, gender=gender)
        user.save()
        return user

    @classmethod
    def get_by_phone(cls, zone_phone):
        return cls.objects(phone=zone_phone).first()

    @classmethod
    def get_by_nickname(cls, nickname):
        return cls.objects(nickname=nickname).first()

    @property
    def finished_info(self):
        return True
