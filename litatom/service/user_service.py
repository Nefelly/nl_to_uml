# coding: utf-8
import random
from copy import deepcopy
import time
import datetime
import logging
import langid
from dateutil.relativedelta import relativedelta
from flask import request

from ..redis import RedisClient
from ..util import (
    validate_phone_number,
    get_time_info,
    time_str_by_ts,
    trunc,
    parse_standard_date,
    format_standard_date,
    get_zero_today,
    filter_emoji
)
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
    OPERATE_TOO_OFTEN,
    REMOVE_EXCHANGE,
    OFFICIAL_AVATAR,
    SPAM_RECORD_NICKNAME_SOURCE,
    SPAM_RECORD_BIO_SOURCE
)

from ..key import (
    REDIS_USER_INFO_FINISHED,
    REDIS_ONLINE_GENDER_REGION,
    REDIS_UID_GENDER,
    REDIS_HUANXIN_ONLINE,
    REDIS_KEY_FORBIDDEN_SESSION_USER
)
from ..model import (
    User,
    UserSetting,
    Feed,
    HuanxinAccount,
    Avatar,
    SocialAccountInfo,
    UserRecord,
    Blocked,
    FaceBookBackup,
    RedisLock,
    ReferralCode,
    UserModel,
    UserAccount,
    BlockedDevices
)
from ..service import (
    SmsCodeService,
    HuanxinService,
    GoogleService,
    FacebookService,
    ForbidCheckService,
    FollowService,
    GlobalizationService,
    MqService,
    AvatarService
)

logger = logging.getLogger(__name__)
sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']
volatile_redis = RedisClient()['volatile']

class UserService(object):
    FORBID_TIME = ONE_MIN
    CREATE_LOCK = 'user_create'
    NICKNAME_LEN_LIMIT = 60
    BIO_ELN_LIMIT = 150
    ERROR_DEVICE_FORBIDDEN = u'Your device has been blocked'

    @classmethod
    def get_all_ids(cls):
        # return [el.user_id for el in UserSetting.objects().only('user_id')]
        return list(volatile_redis.smembers('all_user_ids'))

    @classmethod
    def _trans_session_2_forbidden(cls, user):
        user._set_forbidden_session_cache(user.session_id.replace("session.", ""))
        request.session_id = user.session_id

    @classmethod
    def _trans_forbidden_2_session(cls, user):
        if request.session_id:
            user.generate_new_session(request.session_id.replace("session.", ""))
        elif user.session:
            user.generate_new_session(user.session.replace("session.", ""))

    @classmethod
    def get_forbidden_time_by_uid(cls, user_id):
        user = User.get_by_id(user_id)
        if user:
            cls.should_unforbid(user)
            return time_str_by_ts(user.forbidden_ts)
        return None

    @classmethod
    def device_blocked(cls, uuid):
        return BlockedDevices.is_device_forbidden(uuid)

    @classmethod
    def user_device_blocked(cls, user_id):
        user_setting = UserSetting.get_by_user_id(user_id)
        uuid = user_setting.uuid
        return cls.device_blocked(uuid)

    @classmethod
    def get_followers_by_uid(cls, user_id):
        user = User.get_by_id(user_id)
        if not user:
            return -1
        return user.follower

    @classmethod
    def get_forbidden_error(cls, msg, default_json={}):
        from ..service import AccountService
        error_info = deepcopy(default_json)
        error_info.update({
            'message': msg,
            'forbidden_session': request.session_id,
            'unban_diamonds': AccountService.get_unban_diamonds_by_user_id(request.user_id)
        })
        return error_info

    @classmethod
    def should_unforbid(cls, user):
        if int(time.time()) > user.forbidden_ts:
            user.forbidden = False
            user.save()
            if user.huanxin and user.huanxin.user_id:
                unforbid_status = HuanxinService.active_user(user.huanxin.user_id)
            cls._trans_forbidden_2_session(user)
            return True
        return False

    @classmethod
    def login_job(cls, user):
        """
        登录的动作
        :param user:
        :return:
        """
        if user.forbidden:
            request.user_id = str(user.id)
            if not cls.should_unforbid(user):
                unforbid_time = time_str_by_ts(user.forbidden_ts)
                forbid_info = GlobalizationService.get_region_word('banned_warn')
                request.is_banned = True
                request.session_id = user._set_forbidden_session_cache()
                return forbid_info % unforbid_time, False
        user.generate_new_session()
        user._set_session_cache()
        user._set_huanxin_cache()
        user._set_age_cache()
        if not user.logined:
            user.logined = True
            user.save()
        if user.finished_info:
            cls.refresh_status(str(user.id))
        return None, True

    @classmethod
    def search_user(cls, nickname, user_id):
        res = []
        if not nickname:
            return res, True
        cnt = 0
        max_num = 10
        objs = []
        if len(nickname) <= 3:
            for obj in User.get_users_by_nickname(nickname):
                objs.append(obj)
                cnt += 1
                if cnt >= max_num:
                    break
        else:
            for _ in User.objects(nickname__contains=nickname):
                objs.append(_)
                cnt += 1
                if cnt >= max_num:
                    break
        uids = [str(el.id) for el in objs]
        online_info, status = cls.uids_online(uids)
        if not status:
            online_info = {}
        for _ in objs:
            basic_info = cls.get_basic_info(_)
            uid = str(_.id)
            basic_info['online'] = online_info.get(uid, False)
            basic_info['followed'] = FollowService.in_follow(user_id, uid)
            res.append(basic_info)
        return res, True

    @classmethod
    def _get_words_loc(cls, words):
        for word in words:
            word = filter_emoji(word)
            lang, score = langid.classify(word)
            loc = GlobalizationService.loc_by_lang(lang)
            if loc:
                return loc

    @classmethod
    def is_forbbiden(cls, user_id):
        user = User.get_by_id(user_id)
        return user and user.forbidden

    @classmethod
    def clear_forbidden_session(cls, forbidden_session):
        key = REDIS_KEY_FORBIDDEN_SESSION_USER.format(session=forbidden_session)
        redis_client.delete(key)

    @classmethod
    def unban_user(cls, user_id):
        user = User.get_by_id(user_id)
        if user:
            user.forbidden = False
            user.save()
            if user.huanxin and user.huanxin.user_id:
                HuanxinService.active_user(user.huanxin.user_id)
            cls._trans_forbidden_2_session(user)
            if cls.user_device_blocked(user_id):
                BlockedDevices.remove_forbidden_device(request.uuid)
            return True
        return False

    @classmethod
    def uid_by_huanxin_id(cls, huanxin_id):
        user = User.get_by_huanxin_id(huanxin_id)
        if user:
            return str(user.id)
        return None

    @classmethod
    def _on_create_new_user(cls, user):
        loc = request.loc
        user_id = str(user.id)
        if request.platform:
            user.platform = request.platform
        if loc:
            if user_id:
                UserSetting.create_setting(user_id, loc, request.uuid)
        if not request.uuid:
            return u'your version is too low!', False
        if cls.device_blocked(request.uuid):
            return cls.ERROR_DEVICE_FORBIDDEN, False
        return None, True

    @classmethod
    def _on_update_info(cls, user, data):
        from ..service import ForbidActionService,SpamWordCheckService
        cls.update_info_finished_cache(user)
        gender = data.get('gender', '')
        if gender:
            key = REDIS_UID_GENDER.format(user_id=str(user.id))
            redis_client.set(key, user.gender, ONLINE_LIVE)
        if data.get('birthdate', ''):
            User._set_age_cache(user)
        if user.finished_info:  # need to be last
            cls.refresh_status(str(user.id))
        if getattr(user, 'id', ''):
            # auto move unknown region user to it's lang
            uid = str(user.id)
            nickname = data.get('nickname', '')
            bio = data.get('bio', '')
            # nickname,bio spam word风险拦截
            res = SpamWordCheckService.is_spam_word(nickname)
            if res:
                ForbidActionService.resolve_spam_word(uid,nickname,SPAM_RECORD_NICKNAME_SOURCE)
                return GlobalizationService.get_region_word('alert_msg'), False
            res = SpamWordCheckService.is_spam_word(bio)
            if res:
                ForbidActionService.resolve_spam_word(uid,bio,SPAM_RECORD_BIO_SOURCE)
                return GlobalizationService.get_region_word('alert_msg'), False
            # if (bio or nickname) and GlobalizationService.get_region() == GlobalizationService.DEFAULT_REGION:
            if (bio or nickname):
                cls.check_and_move_to_big(uid, [nickname, bio])
            # if (bio or nickname) and GlobalizationService.get_region() not in GlobalizationService.BIG_REGIONS:
            #     loc = cls._get_words_loc([nickname, bio])
            #     if loc in GlobalizationService.BIG_REGIONS.values():
            #         userSetting = UserSetting.get_by_user_id(uid)
            #         if not userSetting or userSetting.loc_change_times <= 1:
            #             GlobalizationService.change_loc(uid, loc)
            #             userSetting = UserSetting.get_by_user_id(uid)
            #             if userSetting:
            #                 userSetting.loc_change_times += 1
            #                 userSetting.save()
        return None, True
    
    @classmethod
    def check_and_move_to_big(cls, user_id, words):
        if GlobalizationService.get_region() in GlobalizationService.BIG_REGIONS:
            return 
        loc = cls._get_words_loc(words)
        if loc in GlobalizationService.BIG_REGIONS.values():
            userSetting = UserSetting.get_by_user_id(user_id)
            if not userSetting or userSetting.loc_change_times <= 1:
                GlobalizationService.change_loc(user_id, loc)
                userSetting = UserSetting.get_by_user_id(user_id)
                if userSetting:
                    userSetting.loc_change_times += 1
                    userSetting.save()
    
    @classmethod
    def uids_age(cls, user_ids):
        res = {}
        for uid in user_ids:
            res[uid] = cls.uid_age(uid)
        return res

    @classmethod
    def nearest_age_uid(cls, user_id, uids):
        uids = [el for el in uids if el != user_id]
        if not uids:
            return None
        res = uids[0]
        user_age = cls.uid_age(user_id)
        min_dis = abs(cls.uid_age(res) - user_age)
        for uid in uids[1:]:
            age_dis = abs(cls.uid_age(res) - user_age)
            if age_dis < min_dis:
                res = uid
                min_dis = age_dis
        return res

    @classmethod
    def age_in_user_range(cls, user_id, age):
        if not user_id:
            return True
        # if request.region != GlobalizationService.REGION_TH:   # if not in thailand, get out of limit
        #     return True
        user_age = cls.uid_age(user_id)
        interval = 5
        if user_age >= 25:
            if age >= min(25 - interval, 25):
                return True
        elif user_age <= 13 + interval:
            if age <= max(13, user_age + interval):
                return True
        elif age >= user_age - interval and age <= user_age + interval:
            return True
        return False

    @classmethod
    def uid_age(cls, user_id):
        return User.age_by_user_id(user_id)

    @classmethod
    def msg_to_all_users(cls, msg, from_name='Lit official'):
        officail_user = User.get_by_nickname(from_name)
        if not officail_user:
            return False
        huanxin_ids = []
        # msg = u'แอปของเราพบปัญหาระบบแชท เมื่อคุณส่งข้อความไปหาผู้อื่น บางทีอาจจะไม่สำเร็จ ตอนนี้เรารับทราบปัญหาที่เกิดขึ้นแล้ว จะเร่งแก้ไขให้เร็วที่สุด.'
        num = User.objects().count()
        if num >= 200000:
            logger.error('you have too many users, you need to redesign this func')
            return False
        for _ in User.objects():
            if _.huanxin.user_id:
                huanxin_ids.append(_.huanxin.user_id)
        huanxin_ids = [u'love123879348711830'] + huanxin_ids
        # huanxin_ids = [u'love123879348711830']   # joey
        res = HuanxinService.batch_send_msgs(msg, huanxin_ids, officail_user.huanxin.user_id)
        # print res
        return True

    @classmethod
    def msg_to_user(cls, msg, target_user_id):
        from_name = 'Lit official'
        officail_user = User.get_by_nickname(from_name)
        if not officail_user:
            from hendrix.conf import setting
            if setting.IS_DEV:
                officail_user = User.objects().first()
                officail_user.nickname = from_name
                officail_user.save()
            else:
                return False
        user = User.get_by_id(target_user_id)
        if not user:
            return False
        huanxin_ids = [user.huanxin.user_id]
        res = HuanxinService.batch_send_msgs(msg, huanxin_ids, officail_user.huanxin.user_id)
        return True

    @classmethod
    def _huanxin_ids_by_region(cls, region, number=0):
        locs = GlobalizationService.KNOWN_REGION_LOC.get(region, '')
        if number:
            huanxin_ids = []
            loc = locs[0] if isinstance(locs, list) else locs
            for _ in User.objects(country=loc).order_by('-create_time').limit(number):
                if _.huanxin.user_id:
                    huanxin_ids.append(_.huanxin.user_id)
            return huanxin_ids
        all_known_locs = []
        for _ in GlobalizationService.KNOWN_REGION_LOC.values():
            if isinstance(_, list):
                all_known_locs += _
            else:
                all_known_locs.append(_)
        huanxin_ids = []
        if locs:
            real_locs = []
            if not isinstance(locs, list):
                real_locs = [locs]
            else:
                real_locs = locs
            for loc in real_locs:
                for _ in User.objects(country=loc):
                    if _.huanxin.user_id:
                        huanxin_ids.append(_.huanxin.user_id)
        else:
            for _ in User.objects():
                if _.country and _.country not in all_known_locs and _.huanxin.user_id:
                    huanxin_ids.append(_.huanxin.user_id)
        return huanxin_ids

    @classmethod
    def msg_to_region_users(cls, region, msg, number=None):
        # todo  when user gets big  need to redesign
        from_name = 'Lit official'
        officail_user = User.get_by_nickname(from_name)
        if not officail_user:
            return False
        huanxin_ids = ['love123871399047999']
        res = HuanxinService.batch_send_msgs(msg, huanxin_ids, officail_user.huanxin.user_id)
        return True

        num = User.objects().count()
        if num >= 2000000:
            logger.error('you have too many users, you need to redesign this func')
            return False
        huanxin_ids = cls._huanxin_ids_by_region(region, 3 * number)
        if number and number > 0:
            number = min(len(huanxin_ids), number)
            huanxin_ids = random.sample(huanxin_ids, number)
        huanxin_ids = [u'love123879348711830'] + huanxin_ids
        # huanxin_ids = [u'love123879348711830']   # joey
        res = HuanxinService.batch_send_msgs(msg, huanxin_ids, officail_user.huanxin.user_id)
        # print res
        return True

    @classmethod
    def uid_online_by_huanxin(cls, user_ids):
        huanxinid_uid = {}
        to_query = []
        res = {}
        for uid in user_ids:
            huanxinid = User.huanxin_id_by_user_id(uid)
            if huanxinid:
                huanxinid_uid[huanxinid] = uid
                to_query.append(huanxinid)
        query_res = HuanxinService.is_user_online(to_query)
        for huanxinid, status in query_res.items():
            # if status:
            uid = huanxinid_uid[huanxinid]
            res[uid] = status
        # for uid in user_ids:   # not query result, do not deal
        #     if not res.get(uid, False):
        #         res[uid] = False
        return res

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

    # THIS METHOD WITH NO USAGE
    # @classmethod
    # def _forbid(cls, user_id):
    #     forbid_time = cls.FORBID_TIME
    #     if UserRecord.get_forbidden_num_by_uid(user_id) > 0:
    #         forbid_time *= 10
    #     cls.forbid_user(user_id, forbid_time)
    #     return True

    @classmethod
    def forbid_action(cls, user_id, forbid_ts):
        user = User.get_by_id(user_id)
        if not user:
            return False
        forbid_times = UserRecord.get_forbidden_num_by_uid(user_id)
        user.forbidden = True
        user.forbidden_ts = int(time.time()) + forbid_ts * (1 + 5 * forbid_times)
        cls._trans_session_2_forbidden(user)
        user.clear_session()
        for gender in GENDERS:
            # key = REDIS_ONLINE_GENDER.format(gender=gender)
            key = GlobalizationService._online_key_by_region_gender(gender)
            redis_client.zrem(key, user_id)
        redis_client.zrem(GlobalizationService._online_key_by_region_gender(), user_id)
        user.save()
        if user.huanxin and user.huanxin.user_id:
            HuanxinService.deactive_user(user.huanxin.user_id)
        feeds = Feed.objects(user_id=user_id, create_time__gte=int(time.time()) - 3 * ONE_DAY)
        from ..service import FeedService
        for feed in feeds:
            FeedService.remove_from_pub(feed)
            # _.delete()
            feed.change_to_not_shown()
            MqService.push(REMOVE_EXCHANGE, {"feed_id": str(feed.id)})

    @classmethod
    def unban_by_nickname(cls, nickname):
        objs = User.objects(nickname=nickname, forbidden=True)
        if not objs:
            return u'not such forbidden user of: ' + nickname, False
        for el in objs:
            cls.unban_user(str(el.id))
        return None, True

    @classmethod
    def is_official_account(cls, user_id):
        u = User.get_by_id(user_id)
        if u and u.avatar == '5a6989ec-74a2-11e9-977f-00163e02deb4':
            return True
        return False

    @classmethod
    def check_valid_birthdate(cls, birthdate):
        """无效生日均设为18岁"""
        try:
            birth = parse_standard_date(birthdate)
        except:
            return format_standard_date(get_zero_today() - relativedelta(years=18))
        now = get_zero_today()
        if now - relativedelta(years=60) <= birth <= now - relativedelta(years=13):
            return birthdate
        return format_standard_date(now - relativedelta(years=18))

    @classmethod
    def update_info(cls, user_id, data):
        els = ['nickname', 'birthdate', 'avatar', 'bio', 'country', 'referral_code']
        once = ['gender']
        total_fields = els + once
        field_info = u'field must be at least one of: [%s]' % ','.join(total_fields)
        if not data:
            return field_info, False
        for el in data:
            if el not in total_fields or (not data.get(el) and data.get(el) != False):
                return field_info, False
        user = User.get_by_id(user_id)
        if not user:
            return USER_NOT_EXISTS, False
        if 'bio' in data:
            bio = data['bio']
            if len(bio) > cls.BIO_ELN_LIMIT:
                data['bio'] = trunc(bio, cls.BIO_ELN_LIMIT)
        has_nickname = 'nickname' in data
        # if not has_nickname and not user.finished_info:
        #     data['nickname'] = random.choice(['kendall', 'alberti', 'chris', 'asabi', 'bobbie'])
        if has_nickname:
            nick_name = data.get('nickname', '')
            nick_name = nick_name.replace('\r', '').replace('\n', '')
            if len(nick_name) > cls.NICKNAME_LEN_LIMIT:
                nick_name = trunc(nick_name, cls.NICKNAME_LEN_LIMIT)
            if 'LIT' in nick_name.upper():
                if user.avatar != OFFICIAL_AVATAR:
                    return u"illeagal nickname", False
            # if cls.verify_nickname_exists(nick_name):
            #     if not user.finished_info:
            #         nick_name = cls.choose_a_nickname_for_user(nick_name)
            #         if cls.verify_nickname_exists(nick_name):
            #             return u'nickname already exists', False
            #     else:
            #         return u'nickname already exists', False
            data['nickname'] = nick_name
        if data.get('avatar', ''):
            avatar_err = AvatarService.can_change(user_id, data.get('avatar'))
            if avatar_err:
            # if not Avatar.valid_avatar(data.get('avatar')):
                data.pop('avatar')
        gender = data.get('gender', '').strip().replace('\n', '')
        if gender:
            if gender not in GENDERS:
                return u'gender must be one of ' + ','.join(GENDERS), False
            if not Avatar.valid_avatar(data.get('avatar', '')) and not user.avatar:  # user's avatar not set random one
                random_avatars = Avatar.get_avatars()
                if not random_avatars.get(gender):
                    logger.error("random Avatars", random_avatars)
                user.avatar = random.choice(random_avatars.get(gender))
        if data.get('birthdate', ''):
            User.change_age(user_id)
            user.birthdate = cls.check_valid_birthdate(data.get('birthdate'))
            user.save()
            if getattr(request, 'region',
                       '') == GlobalizationService.REGION_IN or request.loc == GlobalizationService.LOC_IN:
                age = User.age_by_user_id(user_id)
                gender = gender if gender else user.gender

                if gender and age >= 0:
                    if (gender == GIRL and age < 15) or (gender == BOY and (age > 21 or age < 19)):
                        GlobalizationService.change_loc(user_id, GlobalizationService.LOC_INN)
        if data.get('referral_code', ''):
            ReferralCode.create(user_id, data.get('referral_code'))
        for el in once:
            if data.get(el, '') and getattr(user, el):
                return u'%s can\'t be reset' % el, False

        for el in data:
            setattr(user, el, data.get(el))
        info, res = cls._on_update_info(user, data)
        if not res:
            return info, False
        # 有关huanxin_service, update_nickname逻辑暂时弃用
        # if has_nickname:
        #     huanxin_id = user.huanxin.user_id
        #     status = True
        #     if len(data.get('nickname')) < cls.NICKNAME_LEN_LIMIT:
        #         status = HuanxinService.update_nickname(huanxin_id, data.get('nickname'))
        user.save()
        return None, True

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
            gender = user.gender if user and user.gender else None
            if gender:
                redis_client.set(key, gender, ONLINE_LIVE)
        return gender

    @classmethod
    def refresh_status(cls, user_id):
        int_time = int(time.time())
        if user_id in [u'5cbc571e3fff2235defd5a65']:  # system account
            cls.set_not_online(user_id)
            return
        pp = redis_client.pipeline()
        pp.zadd(REDIS_HUANXIN_ONLINE, {user_id: int_time})
        pp.get(REDIS_UID_GENDER.format(user_id=user_id))
        _, gender = pp.execute()
        if not gender:
            gender = cls.get_gender(user_id)
        # redis_client.zadd(REDIS_HUANXIN_ONLINE, {user_id: int_time})
        # gender = cls.get_gender(user_id)
        if gender:
            # key = REDIS_ONLINE_GENDER.format(gender=gender)
            key = GlobalizationService._online_key_by_region_gender(gender)
            pp.zadd(key, {user_id: int_time})
            pp.zadd(GlobalizationService._online_key_by_region_gender(), {user_id: int_time})
            pp.execute()
            # redis_client.zadd(key, {user_id: int_time})
            # redis_client.zadd(GlobalizationService._online_key_by_region_gender(), {user_id: int_time})

    @classmethod
    def set_not_online(cls, user_id):
        int_time = int(time.time())
        gender = cls.get_gender(user_id)
        if gender:
            key = REDIS_ONLINE_GENDER_REGION.format(gender=gender, region=GlobalizationService.get_region())
            redis_client.zadd(key, {user_id: int_time - ONLINE_LIVE - 10})

    @classmethod
    def create_huanxin(cls):
        huanxin_id, pwd = HuanxinService.gen_id_pwd()
        if huanxin_id:
            return HuanxinAccount.create(huanxin_id, pwd)
        else:
            return None

    @classmethod
    def uid_online_time(cls, uid):
        key = GlobalizationService._online_key_by_region_gender()
        val = redis_client.zscore(key, uid)
        return int(val) if val else 0

    @classmethod
    def uid_online(cls, uid):
        '''
        :return uid: online map
        :param uids:
        :return:
        '''
        judge_time = int(time.time()) - USER_ACTIVE
        # key = REDIS_ONLINE
        key = GlobalizationService._online_key_by_region_gender()
        score = redis_client.zscore(key, uid)
        if not score or int(score) < judge_time:
            return False
        return True

    @classmethod
    def _uids_score(cls, uids):
        if not isinstance(uids, list):
            return {}
        res = {}
        key = GlobalizationService._online_key_by_region_gender()
        pp = redis_client.pipeline()
        for _ in uids:
            pp.zscore(key, _)
        for uid, score in zip(uids, pp.execute()):
            res[uid] = int(score) if score else 0
        return res

    @classmethod
    def ordered_user_infos(cls, uids, visitor_user_id=None):
        uids_score = cls._uids_score(uids)
        score_lst = [[k, v] for k, v in uids_score.iteritems()]
        sorted_lst = sorted(score_lst, key=lambda x: -x[1])
        res = []
        judge_time = int(time.time()) - USER_ACTIVE
        for uid, online_time in sorted_lst:
            u = User.get_by_id(uid)
            if u:
                info = cls.get_basic_info(u)
                info['online'] = True if online_time >= judge_time else False
                res.append(info)
        return res

    @classmethod
    def uids_online(cls, uids):
        if not isinstance(uids, list):
            return u'wrong user_ids', False
        res = {}
        judge_time = int(time.time()) - USER_ACTIVE
        uids_score = cls._uids_score(uids)
        for uid, score in uids_score.iteritems():
            if score < judge_time:
                res[uid] = False
            else:
                res[uid] = True
            # if _:
            #     score = redis_client.zscore(key, _)
            #     if not score or int(score) < judge_time:
            #         res[_] = False
            #     res[_] = True
        return res, True

    @classmethod
    def check_share_new_user(cls, user_id):
        from .share_stat_service import ShareStatService
        from .ali_log_service import AliLogService
        ip = request.ip
        key = ShareStatService.get_clicker_key(ip)
        if redis_client.exists(key):
            contents = [('action', 'share'), ('remark', 'create_new_user'), ('user_id', user_id), ('user_ip', ip)]
            AliLogService.put_logs(contents)
            redis_client.delete(key)

    @classmethod
    def phone_login(cls, zone, phone, code):
        if phone[0] == '0':
            phone = phone[1:]
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
            huanxin_res = cls.create_huanxin()
            if huanxin_res:
                user.huanxin = huanxin_res
            else:
                return "user create error, please retry", False
            user.phone = zone_phone
            msg, status = cls._on_create_new_user(user)
            if not status:
                return msg, status
            user.save()
            cls.check_share_new_user(str(user.id))
            cls.update_info_finished_cache(user)
            RedisLock.release_mutex(key)
        request.user_id = str(user.id)  # 为了region
        msg, status = cls.login_job(user)
        if not status:
            return msg, False

        basic_info = cls.get_basic_info(user)
        login_info = user.get_login_info()
        basic_info.update(login_info)
        return basic_info, True

    @classmethod
    def google_login(cls, token):
        idinfo = GoogleService.login_info(token, request.platform)
        if not idinfo:
            return u'google login is unavailable now, please try facebook login or login google again ~', False
        google_id = idinfo.get('sub', '')
        if not google_id:
            return u'google login get wrong google id', False
        user = User.get_by_social_account_id(User.GOOGLE_TYPE, google_id)
        if not user:
            key = cls.CREATE_LOCK + google_id
            if not RedisLock.get_mutex(key):
                return OPERATE_TOO_OFTEN, False
            user = User()
            huanxin_res = cls.create_huanxin()
            if not huanxin_res:
                return "user create error, please retry", False
            user.huanxin = huanxin_res
            user.google = SocialAccountInfo.make(google_id, idinfo)
            user.create_time = datetime.datetime.now()
            msg, status = cls._on_create_new_user(user)
            if not status:
                return msg, status
            user.save()
            cls.check_share_new_user(str(user.id))
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
            else:
                huanxin_res = cls.create_huanxin()
                if not huanxin_res:
                    return "user create error, please retry", False
                user.huanxin = huanxin_res
                user.facebook = SocialAccountInfo.make(facebook_id, idinfo)
                user.create_time = datetime.datetime.now()
            msg, status = cls._on_create_new_user(user)
            if not status:
                return msg, status
            user.save()
            cls.check_share_new_user(str(user.id))
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
        login_long = datetime.datetime.now() - user.create_time > datetime.timedelta(days=3)
        word_m = GlobalizationService.get_region_word('bio')
        if login_long:
            key = 'mystierious'
        else:
            key = 'newcomer'
        he_or_she_ind = 0 if user.gender == BOY else 1
        return word_m[key][he_or_she_ind]
        # feed_num = Feed.feed_num(str(user.id))
        # if feed_num < 3:
        #     return u'%s is newcomer~' % he_or_she
        # return u'%s loves to share' % he_or_she

    @classmethod
    def verify_nickname_exists(cls, nickname):  # judge if nickname exists
        if not nickname or User.get_by_nickname(nickname):
            return True
        return False

    @classmethod
    def choose_a_nickname_for_user(cls, nickname):
        chars = [u'\U0001f618', u'\U0001f495', u'\U0001f914', u'\U0001f36d', u'\U0001f497', u'\U0001f619',
                 u'\U0001f61c', u'\U0001f917', u'\U0001f62a', u'\U0001f970', u'\U0001f308', u'\U0001f60f']
        res = nickname
        for i in range(5):
            res += random.choice(chars)
            if not cls.verify_nickname_exists(res):
                return res

    @classmethod
    def uid_online_time_with_huanxin(cls, target_user_id):
        huanxin_time = redis_client.zscore(REDIS_HUANXIN_ONLINE, target_user_id)
        return max(cls.uid_online_time(target_user_id), int(huanxin_time) if huanxin_time else 0)

    @classmethod
    def get_user_info(cls, user_id, target_user_id):
        # msg =  BlockService.get_block_msg(user_id, target_user_id)
        # if msg:
        #     return msg, False
        target_user = User.get_by_id(target_user_id)
        if not target_user:
            return USER_NOT_EXISTS, False
        block_num = UserModel.get_block_num_by_user_id(user_id)
        basic_info = cls.get_basic_info(target_user)
        basic_info.update({
            'be_followed': FollowService.in_follow(target_user_id, user_id),
            'followed': FollowService.in_follow(user_id, target_user_id) if target_user.follower > 0 else False,
            'blocked': Blocked.in_block(user_id, target_user_id, block_num),
            # 'is_blocked': Blocked.in_block(target_user_id, user_id),
            # 'is_followed': Follow.in_follow(target_user_id, user_id)
        })

        basic_info.update(
            {'active_info': get_time_info(cls.uid_online_time_with_huanxin(target_user_id), user_mode=True)}
        )
        if user_id != target_user_id:
            return basic_info, True
        login_info = target_user.get_login_info()
        basic_info.update(login_info)
        basic_info.update({"account_info": UserAccount.get_account_info(user_id), "vip_time": target_user.vip_time})
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
        return AvatarService.get_avatars(request.user_id)

    @classmethod
    def _delete_user(cls, user):
        user_id = str(user.id)
        redis_client.delete(REDIS_USER_INFO_FINISHED.format(user_id=user_id))
        gender = cls.get_gender(user_id)
        if gender:
            # key = REDIS_ONLINE_GENDER.format(gender=gender)
            key = GlobalizationService._online_key_by_region_gender(gender)
            redis_client.zrem(key, user_id)
            # from ..key import REDIS_ANOY_GENDER_ONLINE
            # if user.huanxin and user.huanxin.user_id:
            #     fake_id = user.huanxin.user_id
            #     redis_client.zrem(REDIS_ANOY_GENDER_ONLINE.format(gender=gender), fake_id)
        if user.huanxin and user.huanxin.user_id:
            HuanxinService.delete_user(user.huanxin.user_id)
        redis_client.delete(REDIS_UID_GENDER.format(user_id=user_id))
        redis_client.zrem(GlobalizationService._online_key_by_region_gender(), user_id)
        user.clear_session()
        user.delete()
        user.save()
