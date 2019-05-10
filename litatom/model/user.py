# coding: utf-8
import time
import datetime
import hashlib
import logging
import json
import random
sys_rng = random.SystemRandom()
import urlparse

import re
import json
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
    REDIS_KEY_SESSION_USER,
    REDIS_KEY_USER_HUANXIN,
    REDIS_KEY_USER_AGE
)
from ..const import (
    TWO_WEEKS,
    UNKNOWN_GENDER,
    DEFAULT_QUERY_LIMIT,
    NO_SET
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


class SocialAccountInfo(EmbeddedDocument):
    meta = {
        'strict': False,
    }

    other_id = StringField()
    expires_in = IntField()
    time = DateTimeField(required=True, default=lambda: datetime.datetime.now)
    extra_data = StringField()

    @classmethod
    def make(cls, other_id, payload):
        obj = cls(other_id=other_id, extra_data=json.dumps(payload))
        return obj


class User(Document, UserSessionMixin):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    GOOGLE_TYPE = 'google'
    FACEBOOK_TYPE = 'facebook'
    TYPES = [GOOGLE_TYPE, FACEBOOK_TYPE]
    JUDGES = ['nasty', 'boring', 'like']

    nickname = StringField()
    avatar = StringField()
    gender = StringField()
    birthdate = StringField()   # in form of 1999-12-14 now
    session = StringField()
    sessionCreateTime = DateTimeField()
    logined = BooleanField(default=False)
    bio = StringField()
    phone = StringField()
    country = StringField()
    forbidden = BooleanField(required=True, default=False)
    forbidden_ts = IntField(required=True, default=0)
    follower = IntField(required=True, default=0)
    following = IntField(required=True, default=0)
    judge = ListField(required=True, default=[0, 0, 0])   # nasty, boring, like
    huanxin = EmbeddedDocumentField(HuanxinAccount)
    google = EmbeddedDocumentField(SocialAccountInfo)
    facebook = EmbeddedDocumentField(SocialAccountInfo)
    facebook_ver1 = BooleanField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @property
    def is_forbidden(self):
        if not self.forbidden:
            return False
        if int(time.time()) > self.forbidden_ts:
            self.forbidden = False
            self.save()
            return False
        return True

    def _set_huanxin_cache(self):
        user_id = str(self.id)
        huanxin_id = self.huanxin.user_id
        if not huanxin_id:
            huanxin_id = NO_SET
        key = REDIS_KEY_USER_HUANXIN.format(user_id=user_id)
        redis_client.set(key, huanxin_id, ex=TWO_WEEKS)
        return huanxin_id if huanxin_id != NO_SET else ''

    @classmethod
    def huanxin_id_by_user_id(cls, user_id):
        key = REDIS_KEY_USER_HUANXIN.format(user_id=user_id)
        res = redis_client.get(key)
        if res == NO_SET:
            return ''
        elif not res:
            user = cls.get_by_id(user_id)
            if not user:
                return ''
            res = user._set_huanxin_cache()
        return res

    def _set_age_cache(self):
        user_id = str(self.id)
        if not self.birthdate:
            age = NO_SET
        else:
            age = self.age
        key = REDIS_KEY_USER_AGE.format(user_id=user_id)
        redis_client.set(key, age, ex=TWO_WEEKS)
        return age

    @classmethod
    def age_by_user_id(cls, user_id):
        key = REDIS_KEY_USER_AGE.format(user_id=user_id)
        res = redis_client.get(key)
        if res == NO_SET:
            return 0
        elif not res:
            user = cls.get_by_id(user_id)
            if not user:
                return ''
            res = user._set_age_cache()
        return int(res)

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
        user.create_time = datetime.datetime.now()
        user.save()
        return user

    @classmethod
    def get_by_id(cls, user_id):
        if not bson.ObjectId.is_valid(user_id):
            return None
        return cls.objects(id=user_id).first()

    def add_judge(self, judge):
        if not judge in self.JUDGES:
            return False
        tmp = 0
        for _ in self.JUDGES:
            if judge == _:
                break
            tmp += 1
        self.judge[tmp] += 1
        self.save()

    @classmethod
    def get_by_huanxin_id(cls, huanxinid):
        if not huanxinid:
            return None
        return cls.objects(huanxin__user_id=huanxinid).first()

    @property
    def age(self):
        if not self.birthdate:
            return -1
        date_now = datetime.datetime.now()
        date_birth = datetime.datetime.strptime(self.birthdate, '%Y-%m-%d')
        age = date_now.year - date_birth.year
        try:
            replaced_birth = date_birth.replace(year=date_now.year)
        except ValueError:   # raised when birth date is February 29 and the current year is not a leap year
            replaced_birth = date_birth.replace(year=date_now.year, day=date_birth-1)
        if replaced_birth > date_now:
            return date_now.year - date_birth.year -1
        return date_now.year - date_birth.year
        # year_now = datetime.datetime.now().year
        # return min(year_now - int(self.birthdate.split('-')[0]), 100)

    @classmethod
    def get_by_social_account_id(cls, account_type, account_id):
        if account_type not in cls.TYPES:
            return None
        if account_type == cls.GOOGLE_TYPE:
            return cls.objects(google__other_id=account_id).first()
        elif account_type == cls.FACEBOOK_TYPE:
            return cls.objects(facebook__other_id=account_id).first()

    @classmethod
    def get_by_phone(cls, zone_phone):
        return cls.objects(phone=zone_phone).first()
    
    
    @classmethod
    def chg_follower(cls, user_id, num):
        user = cls.get_by_id(user_id)
        if not user:
            return False
        new = user.follower + num
        user.follower = max(0, new)
        user.save()
        
    @classmethod
    def chg_following(cls, user_id, num):
        user = cls.get_by_id(user_id)
        if not user:
            return False
        new = user.following + num
        user.following = max(0, new)
        user.save()
    
    # @classmethod
    # def huanxin_id_by_user_id(cls, user_id):
    #     user = cls.get_by_id(user_id)
    #     if not user or not user.huanxin:
    #         return None
    #     return user.huanxin.user_id

    @classmethod
    def get_by_nickname(cls, nickname):
        return cls.objects(nickname=nickname).first()

    @property
    def finished_info(self):
        return self.nickname != None and self.gender != None and self.birthdate != None and self.avatar != None
        return True

    def basic_info(self):
        return {
            'user_id': str(self.id),
            'avatar': self.avatar,
            'gender': self.gender if self.gender else UNKNOWN_GENDER,
            'birthdate': self.birthdate,
            'nickname': self.nickname,
            'huanxin_id': self.huanxin.user_id,
            'judged_nasty': self.judge[0],
            'judged_boring': self.judge[1],
            'judged_like': self.judge[2],
            'follower': self.follower,
            'following': self.following

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
    '''
    user's daily records
    '''
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    user_id = StringField(required=True)
    action = StringField(required=True)
    remark = StringField()
    create_date = DateTimeField()
    create_time = IntField(required=True)

    def to_json(self):
        res = {}
        for attr in self._fields:
            if attr == 'id':
                continue
            res[attr] = getattr(self, attr)
        return res

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id).limit(DEFAULT_QUERY_LIMIT)


class UserRecord(Document):
    """
    user's forbidden or other recodrd
    """
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    FORBIDDEN_ACTION = 'forbidden'
    user_id = StringField(required=True)
    action = StringField(required=True)
    create_time = IntField(required=True)

    @classmethod
    def get_forbidden_times_user_id(cls, user_id):
        return cls.objects(action=cls.FORBIDDEN_ACTION, user_id=user_id).count()

    @classmethod
    def add_forbidden(cls, user_id):
        obj = cls()
        obj.user_id = user_id
        obj.action = cls.FORBIDDEN_ACTION
        obj.create_time = int(time.time())
        obj.save()
        return True