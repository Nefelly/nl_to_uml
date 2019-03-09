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
from ..const import (
    TWO_WEEKS,
    UNKNOWN_GENDER
)
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
        return '%d%d' % (ss, rs)
        # if self.finished_info:
        #     return '%d%d' % (ss, rs)
        # return 'N%d%d' % (ss, rs)

    def _purge_session_cache(self):
        key = REDIS_KEY_SESSION_USER.format(session=self.session)
        redis_client.delete(key)

    def _set_session_cache(self, user_id):
        key = REDIS_KEY_SESSION_USER.format(session=self.session)
        redis_client.set(key, user_id, ex=TWO_WEEKS)

    @classmethod
    def get_user_id_by_session(cls, sid):
        key = REDIS_KEY_SESSION_USER.format(session=sid.replace('session.', ''))
        user_id = redis_client.get(key)
        if user_id:
            redis_client.set(key, user_id, ex=TWO_WEEKS)
            return user_id
        return None

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


class HuanxinAccount(EmbeddedDocument):
    user_id = StringField(required=True)
    password = StringField(required=True)

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id).first()

    @classmethod
    def create(cls, user_id, password):
        if not user_id:
            return None
        # obj = cls.get_by_user_id(user_id)
        # if obj:
        #     return obj
        obj = cls()
        obj.user_id = user_id
        obj.password = password
        return obj

    @classmethod
    def get_info(cls, huanxin):
        if not huanxin:
            return {}
        return {
            'user_id': huanxin.user_id,
            'password': huanxin.password
        }



class User(Document, UserSessionMixin):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }


    nickname = StringField()
    avatar = StringField()
    gender = StringField()
    birthdate = StringField()
    session = StringField()
    sessionCreateTime = DateTimeField()
    logined = BooleanField(default=False)
    bio = StringField()
    phone = StringField()
    judge = ListField(default=[0, 0, 0])   # nasty, boring, like
    huanxin = EmbeddedDocumentField(HuanxinAccount)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create_by_phone(cls, nickname, avatar, gender, birthdate, huanxin, zone_phone):
        user = cls.get_by_phone(zone_phone)
        if not user:
            user = cls()
        user.huanxin = huanxin
        user.nickname = nickname
        user.avatar = avatar
        user.gender = gender
        user.birthdate = birthdate
        user.phone = zone_phone
        user.save()
        return user

    @classmethod
    def get_by_id(cls, user_id):
        if not bson.ObjectId.is_valid(user_id):
            return None
        return cls.objects(id=user_id).first()

    @classmethod
    def get_by_phone(cls, zone_phone):
        return cls.objects(phone=zone_phone).first()

    @classmethod
    def huanxin_id_by_user_id(cls, user_id):
        user = cls.get_by_id(user_id)
        if not user or not user.huanxin:
            return None
        return user.huanxin.user_id

    @classmethod
    def get_by_nickname(cls, nickname):
        return cls.objects(nickname=nickname).first()

    @property
    def finished_info(self):
        return self.nickname != None and self.gender != None and self.birthdate != None
        return True

    def basic_info(self):
        return {
            'user_id': str(self.id),
            'avatar': self.avatar,
            'gender': self.gender if self.gender else UNKNOWN_GENDER,
            'birthdate': self.birthdate,
            'nickname': self.nickname,
            'huanxin_id': self.huanxin.user_id

        }

    def get_login_info(self):
        return {
            'session': self.session_id,
            'finished_info': self.finished_info,
            'is_first_login': not self.logined,
            'huanxin': HuanxinAccount.get_info(self.huanxin)
        }


class UserSetting(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    user_id = StringField()
    lang = StringField()


class UserAction(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    user_id = StringField()
    action = StringField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)