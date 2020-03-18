# coding: utf-8
import time
import datetime
import hashlib
import logging
import json
import random
import cPickle

sys_rng = random.SystemRandom()
import urlparse

import re
import json
import bson
import TLSSigAPIv2
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
    REDIS_KEY_USER_AGE,
    REDIS_USER_CACHE,
    REDIS_USER_SETTING_CACHE,
    REDIS_USER_MODEL_CACHE,
    REDIS_KEY_FORBIDDEN_SESSION_USER
)
from ..const import (
    TWO_WEEKS,
    ONE_DAY,
    UNKNOWN_GENDER,
    DEFAULT_QUERY_LIMIT,
    NO_SET,
    USER_ACTIVE,
    SYS_FORBID,
    MANUAL_FORBID,
)
from ..redis import RedisClient
from ..util import (
    format_standard_time,
    unix_ts_local,
    passwdhash,
    date_to_int_time
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

    @classmethod
    def _is_valid_session(cls, pure_session):
        return len(pure_session) == 19 and pure_session.startswith('12')

    def _purge_session_cache(self):
        key = REDIS_KEY_SESSION_USER.format(session=self.session)
        redis_client.delete(key)

    def _set_session_cache(self):
        key = REDIS_KEY_SESSION_USER.format(session=self.session)
        expire_time = 60 * ONE_DAY if self.phone else TWO_WEEKS
        redis_client.set(key, str(self.id), ex=expire_time)

    def _set_forbidden_session_cache(self, session=None):
        if session:
            session = session.replace("session.", "")
        forbidden_session = self._build_session_string() if not session else session
        key = REDIS_KEY_FORBIDDEN_SESSION_USER.format(session=forbidden_session)
        redis_client.delete(key)
        redis_client.set(key, str(self.id), ex=TWO_WEEKS)
        return self.SESSION_ID_PATTERN.format(id=forbidden_session)

    def clear_session(self):
        if not self.session:
            return
        self._purge_session_cache()
        self.session = None
        self.save()

    def generate_new_session(self, session=None):
        self.clear_session()
        self.session = self._build_session_string() if not session else session
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


class BlockedDevices(Document):
    meta = {
        'strict': False,
    }
    uuid = StringField(required=True)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def add_device(cls, uuid):
        if cls.get_by_device(uuid):
            return True
        obj = cls()
        obj.uuid = uuid
        obj.save()

    @classmethod
    def get_by_device(cls, uuid):
        obj = cls.objects(uuid=uuid).first()
        return obj


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


def base64_decode_url(base64_data):
    import base64
    """ base url decode 实现"""
    base64_data_str = bytes.decode(base64_data)
    base64_data_str = base64_data_str.replace('*', '+')
    base64_data_str = base64_data_str.replace('-', '/')
    base64_data_str = base64_data_str.replace('_', '=')
    raw_data = base64.b64decode(base64_data_str)
    return raw_data


class User(Document, UserSessionMixin):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    GOOGLE_TYPE = 'google'
    FACEBOOK_TYPE = 'facebook'
    TYPES = [GOOGLE_TYPE, FACEBOOK_TYPE]
    JUDGES = ['nasty', 'boring', 'like']
    DEFUALT_AGE = 0

    SDKAPPID = '1400288794'
    KEY = '9570e67ffeecd5432059ce871c267507a28418f4ab91cea5f4f89d0e6ecb137f'
    TENCENT_SIG_EXPIRE = 18000 * 86400
    # tencent_user_sig = StringField(default='')
    # user_sig_expire_at = IntField(default=0)

    nickname = StringField()
    avatar = StringField()
    gender = StringField()
    birthdate = StringField()  # in form of 1999-12-14 now
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
    judge = ListField(required=True, default=[0, 0, 0])  # nasty, boring, like
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

    @property
    def user_sig(self):
        # time_now = int(time.time())
        # if self.user_sig_expire_at > time_now:
        #     if self.tencent_user_sig:
        #         return self.tencent_user_sig
        api = TLSSigAPIv2.TLSSigAPIv2(self.SDKAPPID, self.KEY)
        sig = api.gen_sig(self.huanxin.user_id, self.TENCENT_SIG_EXPIRE)
        # self.tencent_user_sig = sig
        # self.user_sig_expire_at = time_now + self.TENCENT_SIG_EXPIRE
        # self.save()
        return sig

    @classmethod
    def get_user_id_by_session(cls, sid):
        pure_session = sid.replace('session.', '')
        key = REDIS_KEY_SESSION_USER.format(session=pure_session)
        user_id = redis_client.get(key)
        if user_id:
            # redis_client.set(key, user_id, ex=TWO_WEEKS)
            return user_id
        else:
            if not cls._is_valid_session(pure_session):
                return None
            obj = cls.objects(session=pure_session).first()
            if not obj:
                return None
            obj._set_session_cache()
            return str(obj.id)
        return None

    @classmethod
    def get_forbidden_user_id_by_session(cls, sid):
        pure_session = sid.replace('session.', '')
        key = REDIS_KEY_FORBIDDEN_SESSION_USER.format(session=pure_session)
        user_id = redis_client.get(key)
        if user_id:
            return user_id
        return None

    @classmethod
    def user_register_yesterday(cls, gender, country):
        now = datetime.datetime.now()
        zeroToday = now - datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second,
                                             microseconds=now.microsecond)
        zeroYestoday = zeroToday - datetime.timedelta(days=1)
        return list(
            User.objects(create_time__gte=zeroYestoday, create_time__lte=zeroToday, gender=gender, country=country))

    @classmethod
    def info_by_session(cls, sid):
        user_id = cls.get_user_id_by_session(sid)
        if user_id:
            return cls.get_by_id(user_id).to_json()
        return None

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
    def _age_by_cache(cls, res):
        return int(res) if res != NO_SET and res else cls.DEFUALT_AGE

    @classmethod
    def age_by_user_id(cls, user_id):
        key = REDIS_KEY_USER_AGE.format(user_id=user_id)
        res = redis_client.get(key)
        if res == NO_SET:
            return cls.DEFUALT_AGE
        elif not res:
            user = cls.get_by_id(user_id)
            if not user:
                return cls.DEFUALT_AGE
            res = user._set_age_cache()
        return cls._age_by_cache(res)

    @classmethod
    def batch_age_by_user_ids(cls, target_uids):
        target_uids = [_ for _ in target_uids if _]
        keys = [REDIS_KEY_USER_AGE.format(user_id=_) for _ in target_uids]
        m = {}
        for uid, age in zip(target_uids, redis_client.mget(keys)):
            if not age:
                age = cls.age_by_user_id(uid)
            else:
                age = cls._age_by_cache(age)
            m[uid] = age
        return m

    @classmethod
    def change_age(cls, user_id):
        key = REDIS_KEY_USER_AGE.format(user_id=user_id)
        redis_client.delete(key)

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
    def _disable_cache(cls, user_id):
        redis_client.delete(REDIS_USER_CACHE.format(user_id=user_id))

    @classmethod
    def get_by_id(cls, user_id):
        cache_key = REDIS_USER_CACHE.format(user_id=user_id)
        cache_obj = redis_client.get(cache_key)
        if cache_obj:
            # redis_client.incr('user_cache_hit_cnt')
            return cPickle.loads(cache_obj)
        if not bson.ObjectId.is_valid(user_id):
            return None
        obj = cls.objects(id=user_id).first()
        # redis_client.incr('user_cache_miss_cnt')
        redis_client.set(cache_key, cPickle.dumps(obj), USER_ACTIVE)
        return obj

    def save(self, *args, **kwargs):
        if getattr(self, 'id', ''):
            self._disable_cache(str(self.id))
        super(User, self).save(*args, **kwargs)

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
    def days(self):
        return (datetime.datetime.now() - self.create_time).days

    @property
    def age(self):
        if not self.birthdate:
            return -1
        date_now = datetime.datetime.now()
        try:
            date_birth = datetime.datetime.strptime(self.birthdate, '%Y-%m-%d')
        except:
            date_birth = datetime.datetime.now()
        age = date_now.year - date_birth.year
        try:
            replaced_birth = date_birth.replace(year=date_now.year)
        except ValueError:  # raised when birth date is February 29 and the current year is not a leap year
            replaced_birth = date_birth.replace(year=date_now.year, day=date_birth.day - 1)
        if replaced_birth > date_now:
            return date_now.year - date_birth.year - 1
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

    @classmethod
    def get_by_create_time(cls, from_time, to_time):
        return cls.objects(create_time__gte=from_time, create_time__lte=to_time)

    @property
    def finished_info(self):
        return self.nickname != None and self.gender != None and self.birthdate != None and self.avatar != None
        return True

    def delete(self, *args, **kwargs):
        if getattr(self, 'id', ''):
            self._disable_cache(str(self.id))
        super(User, self).delete(*args, **kwargs)

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
            'following': self.following,
            'age': self.age_by_user_id(str(self.id))

        }

    def get_login_info(self):
        return {
            'session': self.session_id,
            'finished_info': self.finished_info,
            'is_first_login': not self.logined,
            'create_time': date_to_int_time(self.create_time),
            'huanxin': HuanxinAccount.get_info(self.huanxin),
            'user_sig': self.user_sig
        }


class OnlineLimit(EmbeddedDocument):
    meta = {
        'strict': False
    }
    age_low = IntField()
    age_high = IntField()
    gender = StringField()
    is_new = BooleanField(default=False)

    @classmethod
    def make(cls, age_low, age_high, gender, is_new):
        obj = cls()
        if age_low:
            obj.age_low = age_low
        if age_high:
            obj.age_high = age_high
        if gender:
            obj.gender = gender
        obj.is_new = is_new
        return obj

    def to_json(self):
        return {
            'age_low': self.age_low,
            'age_high': self.age_high,
            'gender': self.gender,
            'is_new': self.is_new
        }


class UserSetting(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    user_id = StringField(required=True, unique=True)
    lang = StringField(required=True, default='')
    uuid = StringField()
    loc_change_times = IntField(default=0)

    good_rate_times = IntField(default=0)
    online_limit = EmbeddedDocumentField(OnlineLimit)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_user_id(cls, user_id):
        cache_key = REDIS_USER_SETTING_CACHE.format(user_id=user_id)
        cache_obj = redis_client.get(cache_key)
        if cache_obj:
            # redis_client.incr('setting_cache_hit_cnt')
            return cPickle.loads(cache_obj)
        obj = cls.objects(user_id=user_id).first()
        # redis_client.incr('setting_cache_miss_cnt')
        redis_client.set(cache_key, cPickle.dumps(obj), USER_ACTIVE)
        return obj

    @classmethod
    def batch_get_by_user_ids(cls, user_ids):
        user_ids = [_ for _ in user_ids if _]
        keys = [REDIS_USER_SETTING_CACHE.format(user_id=_) for _ in user_ids]
        m = {}
        for uid, obj in zip(user_ids, redis_client.mget(keys)):
            if not obj:
                obj = cls.get_by_user_id(uid)
            else:
                obj = cPickle.loads(obj)
            m[uid] = obj
        return m

    @classmethod
    def _disable_cache(cls, user_id):
        redis_client.delete(REDIS_USER_SETTING_CACHE.format(user_id=user_id))

    def save(self, *args, **kwargs):
        if getattr(self, 'user_id', ''):
            self._disable_cache(str(self.user_id))
        super(UserSetting, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if getattr(self, 'user_id', ''):
            self._disable_cache(str(self.user_id))
        super(UserSetting, self).delete(*args, **kwargs)

    @classmethod
    def create_setting(cls, user_id, lang, uuid=None):
        if cls.get_by_user_id(user_id):
            return True
        obj = cls()
        obj.user_id = user_id
        obj.lang = lang
        if uuid:
            obj.uuid = uuid
        obj.save()
        user = User.get_by_id(user_id)
        if user:
            user.country = lang
            user.save()
        return True

    @classmethod
    def ensure_setting(cls, user_id, lang, uuid):
        obj = cls.get_by_user_id(user_id)
        if not obj:
            cls.create_setting(user_id, lang, uuid)
        else:
            obj.lang = lang
            obj.save()
        return True


class UserAddressList(Document):
    '''
    user's daily records
    '''
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    user_id = StringField(required=True)
    phones = StringField(required=True)
    user_phone = StringField()
    create_time = IntField(required=True)

    def to_json(self):
        res = {}
        for attr in self._fields:
            if attr == 'id':
                continue
            res[attr] = getattr(self, attr)
        return res

    @classmethod
    def upsert(cls, user_id, phones, user_phone):
        obj = cls.get_by_user_id(user_id)
        if not obj:
            obj = cls()
            obj.user_id = user_id
        if phones:
            obj.phones = phones
        if user_phone:
            obj.user_phone = user_phone
        obj.create_time = int(time.time())
        obj.save()

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.objects(user_id=user_id).first()


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
    other_user_id = StringField()
    amount = IntField()
    remark = StringField()
    version = StringField()
    create_date = DateTimeField()
    create_time = IntField(required=True)

    @classmethod
    def create(cls, user_id, action, other_user_id=None, amount=None, remark=None, version=None):
        userAction = cls()
        userAction.user_id = user_id
        userAction.action = action
        if remark:
            userAction.remark = remark
        if other_user_id:
            userAction.other_user_id = other_user_id
        if amount:
            userAction.amount = amount
        if version:
            userAction.version = version
        userAction.create_time = int(time.time())
        userAction.create_date = datetime.datetime.now()
        userAction.save()
        return True

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
    user_id = StringField(required=True)
    action = StringField(required=True)
    create_time = IntField(required=True)

    @classmethod
    def get_forbidden_times_user_id(cls, user_id):
        return cls.objects(user_id=user_id).count()

    @classmethod
    def get_forbid_users_by_time(cls, from_ts, to_ts):
        return cls.objects(create_time__gte=from_ts, create_time__lte=to_ts)

    @classmethod
    def add_forbidden(cls, user_id):
        obj = cls()
        obj.user_id = user_id
        obj.action = MANUAL_FORBID
        obj.create_time = int(time.time())
        obj.save()
        return True

    @classmethod
    def add_sys_forbidden(cls, user_id):
        obj = cls()
        obj.user_id = user_id
        obj.action = SYS_FORBID
        obj.create_time = int(time.time())
        obj.save()
        return True
