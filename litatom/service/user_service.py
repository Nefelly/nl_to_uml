# coding: utf-8
import random
import time
import datetime
from flask import request

from ..redis import RedisClient
from ..util import (
    validate_phone_number,
    time_str_by_ts)
from ..const import (
    TWO_WEEKS,
    ONE_DAY,
    ONE_MIN,
    USER_NOT_EXISTS,
    BOY,
    GIRL,
    GENDERS,
    ONLINE_LIVE,
    USER_ACTIVE,
    FORBID_INFO,
    OPERATE_TOO_OFTEN

)

from ..key import (
    REDIS_USER_INFO_FINISHED,
    REDIS_ONLINE_GENDER,
    REDIS_UID_GENDER,
    REDIS_ONLINE
)
from ..model import (
    User,
    Feed,
    HuanxinAccount,
    Avatar,
    SocialAccountInfo,
    UserRecord,
    Follow,
    Blocked,
    FaceBookBackup,
    RedisLock
)
from ..service import (
    SmsCodeService,
    HuanxinService,
    GoogleService,
    FacebookService,
    BlockService
)

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

class UserService(object):
    FORBID_TIME = ONE_MIN
    CREATE_LOCK = 'user_create'
    @classmethod
    def login_job(cls, user):
        """
        登录的动作
        :param user:
        :return:
        """
        if user.forbidden:
            if False and int(time.time()) > user.forbidden_ts:
                user.forbidden = False
                user.save()
                if user.huanxin and user.huanxin.user_id:
                    HuanxinService.active_user(user.huanxin.user_id)
            else:
                unforbid_time = time_str_by_ts(user.forbidden_ts)
                return FORBID_INFO.format(unforbid_time=unforbid_time), False
        user.generate_new_session()
        user._set_session_cache(str(user.id))
        if not user.logined:
            user.logined = True
            user.save()
        if user.finished_info:
            cls.refresh_status(str(user.id))
        return None, True

    @classmethod
    def _on_update_info(cls, user, data):
        cls.update_info_finished_cache(user)
        if user.finished_info:
            cls.refresh_status(str(user.id))
        gender = data.get('gender', '')
        if gender:
            key = REDIS_UID_GENDER.format(user_id=str(user.id))
            redis_client.set(key, user.gender, ONLINE_LIVE)

    @classmethod
    def query_user_info_finished(cls, user_id):
        key = REDIS_USER_INFO_FINISHED.format(user_id=str(user_id))
        res = redis_client.get(key)
        if not res:
            user = User.get_by_id(user_id)
            if not user:
                return False
            return cls.update_info_finished_cache(user) == 1
        else:
            res = int(res)
        return res == 1

    @classmethod
    def user_info_by_uid(cls, user_id):
        user = User.get_by_id(user_id)
        if not user:
            return {}
        return cls.get_basic_info(user)

    @classmethod
    def nickname_by_uid(cls, user_id):
        user = User.get_by_id(user_id)
        if not user:
            return ''
        return user.nickname

    @classmethod
    def user_infos_by_huanxinids(cls, ids):
        if not ids or not isinstance(ids, list):
            return u'wrong arguments, exp: {ids:[1,2,3]}', False
        res = {}
        ids = ids
        for _ in ids:
            u = User.get_by_huanxin_id(_)
            res[_] = cls.get_basic_info(u)
        return res, True

    @classmethod
    def _forbid(cls, user_id):
        forbid_time = cls.FORBID_TIME
        if UserRecord.get_forbidden_times_user_id(user_id) > 0:
            forbid_time *= 10
        cls.forbid_user(user_id, forbid_time)
        return True

    @classmethod
    def forbid_user(cls, user_id, forbid_ts):
        user = User.get_by_id(user_id)
        if not user:
            return False
        user.forbidden = True
        user.forbidden_ts = int(time.time()) + forbid_ts
        user.clear_session()
        for gender in GENDERS:
            key = REDIS_ONLINE_GENDER.format(gender=gender)
            redis_client.zrem(key, user_id)
        redis_client.zrem(REDIS_ONLINE, user_id)
        user.save()
        if user.huanxin and user.huanxin.user_id:
            HuanxinService.deactive_user(user.huanxin.user_id)
        UserRecord.add_forbidden(user_id)
        return True

    @classmethod
    def update_info(cls, user_id, data):
        els = ['nickname', 'birthdate', 'avatar', 'bio', 'country']
        once = ['gender']
        total_fields = els + once
        field_info = u'field must be at least one of: [%s]' % ','.join(total_fields)
        if not data:
            return field_info, False
        for el in data:
            if el not in total_fields or (not data.get(el) and data.get(el) != False):
                return field_info, False
        has_nickname = 'nickname' in data
        if has_nickname:
            nick_name = data.get('nickname', '')
            if cls.verify_nickname_exists(nick_name):
                return u'nickname already exists', False
            nick_name = nick_name.replace('\r', '').replace('\n', '')
            data['nickname'] = nick_name
        user = User.get_by_id(user_id)
        if not user:
            return USER_NOT_EXISTS, False
        if data.get('avatar', ''):
            if not Avatar.valid_avatar(data.get('avatar')):
                data.pop('avatar')
        for el in once:
            if data.get(el, '') and getattr(user, el):
                return u'%s can\'t be reset' % el, False
        gender = data.get('gender', '')
        if gender:
            if gender not in GENDERS:
                return u'gender must be one of ' + ',' . join(GENDERS), False
            if not Avatar.valid_avatar(data.get('avatar', '')) and not user.avatar:   # user's avatar not set random one
                user.avatar = random.choice(Avatar.get_avatars()[gender])
        for el in data:
            setattr(user, el, data.get(el))
        status = True
        if has_nickname:
            huanxin_id = user.huanxin.user_id
            status = HuanxinService.update_nickname(huanxin_id, data.get('nickname'))
        if status:
            cls._on_update_info(user, data)
            user.save()
            return None, True
        else:
            return u'update huanxin nickname failed', False

    @classmethod
    def update_info_finished_cache(cls, user):
        key = REDIS_USER_INFO_FINISHED.format(user_id=str(user.id))
        res = 1 if user.finished_info else 0
        redis_client.set(key, res, ex=TWO_WEEKS + ONE_DAY)
        return res

    @classmethod
    def get_gender(cls, user_id):
        key = REDIS_UID_GENDER.format(user_id=user_id)
        gender = redis_client.get(key)
        if not gender:
            user = User.get_by_id(user_id)
            gender = user.gender if user.gender else None
        if gender:
            redis_client.set(key, gender, ONLINE_LIVE)
        return gender

    @classmethod
    def refresh_status(cls, user_id):
        int_time = int(time.time())
        gender = cls.get_gender(user_id)
        if gender:
            key = REDIS_ONLINE_GENDER.format(gender=gender)
            redis_client.zadd(key, {user_id: int_time})
            redis_client.zadd(REDIS_ONLINE, {user_id: int_time})
            if int_time % 100 == 0:
                redis_client.zremrangebyscore(key, -1, int_time - ONLINE_LIVE)

    @classmethod
    def create_huanxin(cls):
        huanxin_id, pwd = HuanxinService.gen_id_pwd()
        return HuanxinAccount.create(huanxin_id, pwd)

    @classmethod
    def uid_online(cls, uid):
        '''
        :return uid: online map
        :param uids:
        :return:
        '''
        judge_time = int(time.time()) - USER_ACTIVE
        key = REDIS_ONLINE
        score = redis_client.zscore(key, uid)
        if not score or int(score) < judge_time:
            return False
        return True

    @classmethod
    def uids_online(cls, uids):
        if not isinstance(uids, list):
            return u'wrong user_ids', False
        res = {}
        for _ in uids:
            if _:
                res[_] = cls.uid_online(_)
        return res, True

    @classmethod
    def phone_login(cls, zone, phone, code):
        msg, status = SmsCodeService.verify_code(zone, phone, code)
        if not status:
            return msg, status
        zone_phone = validate_phone_number(zone + phone)
        if not zone_phone:
            return cls.ERR_WORONG_TELEPHONE, False
        user = User.get_by_phone(zone_phone)
        if not user:
            key = cls.CREATE_LOCK + zone_phone
            if not RedisLock.get_mutex(key):
                return OPERATE_TOO_OFTEN, False
            user = User()
            user.huanxin = cls.create_huanxin()
            user.phone = zone_phone
            user.save()
            cls.update_info_finished_cache(user)
            RedisLock.release_mutex(key)
        msg, status = cls.login_job(user)
        if not status:
            return msg, False

        basic_info = cls.get_basic_info(user)
        login_info = user.get_login_info()
        basic_info.update(login_info)
        return basic_info, True

    @classmethod
    def google_login(cls, token):
        idinfo = GoogleService.login_info(token)
        if not idinfo:
            return u'google login check false', False
        google_id = idinfo.get('sub', '')
        if not google_id:
            return u'google login get wrong google id', False
        user = User.get_by_social_account_id(User.GOOGLE_TYPE, google_id)
        if not user:
            key = cls.CREATE_LOCK + google_id
            if not RedisLock.get_mutex(key):
                return OPERATE_TOO_OFTEN, False
            user = User()
            user.huanxin = cls.create_huanxin()
            user.google = SocialAccountInfo.make(google_id, idinfo)
            user.create_time = datetime.datetime.now()
            user.save()
            cls.update_info_finished_cache(user)
            RedisLock.release_mutex(key)
        msg, status = cls.login_job(user)
        if not status:
            return msg, False

        basic_info = cls.get_basic_info(user)
        login_info = user.get_login_info()
        basic_info.update(login_info)
        return basic_info, True

    @classmethod
    def facebook_login(cls, token):
        idinfo = FacebookService.login_info(token)
        if not idinfo:
            return u'facebook login check false', False
        facebook_id = idinfo.get('id', '')
        if not facebook_id:
            return u'facebook login get wrong facebook id', False
        user = User.get_by_social_account_id(User.FACEBOOK_TYPE, facebook_id)
        if not user:
            key = cls.CREATE_LOCK + facebook_id
            if not RedisLock.get_mutex(key):
                return OPERATE_TOO_OFTEN, False
            obj = FaceBookBackup.objects(nickname=idinfo.get('name')).first()
            user = User()
            if obj:
                oldUser = User.get_by_id(obj.uid)
                for attr in oldUser._fields:
                    if attr not in ['id', 'facebook_ver1', 'facebook']:
                        setattr(user, attr, getattr(oldUser, attr))
                user.facebook = SocialAccountInfo.make(facebook_id, idinfo)
                user.save()
            else:
                user.huanxin = cls.create_huanxin()
                user.facebook = SocialAccountInfo.make(facebook_id, idinfo)
                user.create_time = datetime.datetime.now()
                user.save()
            cls.update_info_finished_cache(user)
            RedisLock.release_mutex(key)
        msg, status = cls.login_job(user)
        if not status:
            return msg, False

        basic_info = cls.get_basic_info(user)
        login_info = user.get_login_info()
        basic_info.update(login_info)
        return basic_info, True
    
    @classmethod
    def get_basic_info(cls, user):
        if not user:
            return {}
        if request.ip_should_filter:
            if user.age < 18:
                return {}
        basic_info = user.basic_info()
        basic_info.update({'bio': cls.get_bio(user)})
        return basic_info

    @classmethod
    def get_bio(cls, user):
        '''
        !!!! attention, cal bio is too mongo expensive should be in user
        :param user:
        :return:
        '''
        if user.bio:
            return user.bio
        feed_num = Feed.feed_num(str(user.id))
        he_or_she = 'He' if user.gender == BOY else 'She'
        if feed_num < 3:
            return u'%s is mysterious~' % he_or_she
        return u'%s loves to share' % he_or_she

    @classmethod
    def verify_nickname_exists(cls, nickname):   # judge if nickname exists
        if not nickname or User.get_by_nickname(nickname):
            return True
        return False

    @classmethod
    def get_user_info(cls, user_id, target_user_id):
        # msg =  BlockService.get_block_msg(user_id, target_user_id)
        # if msg:
        #     return msg, False
        target_user = User.get_by_id(target_user_id)
        if not target_user:
            return USER_NOT_EXISTS, False
        basic_info = cls.get_basic_info(target_user)
        basic_info.update({
            'followed': Follow.in_follow(user_id, target_user_id),
            'blocked': Blocked.in_block(user_id, target_user_id)
        })
        if user_id != target_user_id:
            return basic_info, True
        login_info = target_user.get_login_info()
        basic_info.update(login_info)
        return basic_info, True

    @classmethod
    def batch_get_user_info_m(cls, uids):
        res_m = {}
        for uid in uids:
            if res_m.has_key(uid):
                continue
            user = User.get_by_id(uid)
            if user:
                res_m[uid] = user.basic_info()
        return res_m

    @classmethod
    def get_avatars(cls):
        return Avatar.get_avatars()

    @classmethod
    def _delete_user(cls, user):
        user_id = str(user.id)
        redis_client.delete(REDIS_USER_INFO_FINISHED.format(user_id=user_id))
        gender = cls.get_gender(user_id)
        if gender:
            key = REDIS_ONLINE_GENDER.format(gender=gender)
            redis_client.zrem(key, user_id)
            from ..key import REDIS_ANOY_GENDER_ONLINE
            if user.huanxin and user.huanxin.user_id:
                fake_id = user.huanxin.user_id
                redis_client.zrem(REDIS_ANOY_GENDER_ONLINE.format(gender=gender), fake_id)
        if user.huanxin and user.huanxin.user_id:
            HuanxinService.delete_user(user.huanxin.user_id)
        redis_client.delete(REDIS_UID_GENDER.format(user_id=user_id))
        redis_client.zrem(REDIS_ONLINE, user_id)
        user.clear_session()
        user.delete()
        user.save()
