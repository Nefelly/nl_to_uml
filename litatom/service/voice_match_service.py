# coding: utf-8
import time
import datetime
import random
from hendrix.conf import setting
from ..redis import RedisClient
from flask import (
    request
)
from ..key import (
    REDIS_USER_VOICE_MATCH_LEFT,
    REDIS_VOICE_FAKE_ID_UID,
    REDIS_VOICE_UID_FAKE_ID,
    REDIS_VOICE_FAKE_START,
    REDIS_VOICE_ANOY_CHECK_POOL,
    REDIS_VOICE_MATCH_PAIR,
    REDIS_VOICE_MATCHED_BEFORE,
    REDIS_VOICE_MATCHED,
    REDIS_VOICE_FAKE_LIKE,
    REDIS_VOICE_JUDGE_LOCK
)
from ..util import (
    now_date_key,
    low_high_pair
)
from ..const import (
    CREATE_HUANXIN_ERROR,
    ONE_DAY,
    FIVE_MINS,
    GENDERS,
    BOY,
    GIRL,
    MAX_TIME,
    USER_NOT_EXISTS,
    PROFILE_NOT_COMPLETE,
    NOT_IN_MATCH
)
from ..service import (
    UserService,
    FollowService,
    BlockService,
    GlobalizationService,
    UserFilterService
)
from ..model import User
redis_client = RedisClient()['lit']

class VoiceMatchService(object):
    MAX_TIME = 10 ** 13
    MATCH_WAIT = 60 * 7 + 1
    MATCH_INT = 60 * 7  # talking time
    TOTAL_WAIT = MATCH_INT + MATCH_WAIT + FIVE_MINS
    MAX_CHOOSE_NUM = 100
    MATCH_TMS = 5 if not setting.IS_DEV else 1000
    OTHER_GENDER_M = {BOY: GIRL, GIRL: BOY}

    @classmethod
    def _get_voice_id(cls, user):
        huanxin = user.huanxin
        return huanxin.user_id, huanxin.password
        # return HuanxinService.gen_id_pwd()

    @classmethod
    def get_tips(cls):
        word = GlobalizationService.get_region_word('voice_match_msg')
        data = {
            'chat_time': cls.MATCH_INT,
            BOY: [word],
            GIRL: [word],
            'top_wording': GlobalizationService.get_region_word('voice_top_wording')
        }
        return data, True


    @classmethod
    def _add_to_match_pool(cls, gender, fake_id):
        # 进入匹配id池子
        if not gender or not fake_id:
            return
        int_time = int(time.time())
        # voice_gender_key = REDIS_ANOY_GENDER_ONLINE.format(gender=gender)
        voice_gender_key = GlobalizationService.voice_match_key_by_region_gender(gender)
        redis_client.zadd(voice_gender_key,{fake_id: int_time} )

    @classmethod
    def _remove_from_match_pool(cls, gender, fake_id):
        if not gender or not fake_id:
            return
        return redis_client.zrem(GlobalizationService.voice_match_key_by_region_gender(gender), fake_id)

    @classmethod
    def _add_to_check_pool(cls, fake_id):
        if not fake_id:
            return
        int_time = int(time.time())
        redis_client.zadd(REDIS_VOICE_ANOY_CHECK_POOL, {fake_id: int_time})

    @classmethod
    def _destroy_fake_id(cls, fake_id, need_remove_from_pool=True):
        if not fake_id:
            return
        #HuanxinService.delete_user(fake_id)
        user_id = redis_client.get(REDIS_VOICE_FAKE_ID_UID.format(fake_id=fake_id))

        if user_id:
            # could not be clear now, because should be used to judge
            # redis_client.delete(REDIS_VOICE_FAKE_ID_UID.format(fake_id=fake_id))
            redis_client.delete(REDIS_VOICE_JUDGE_LOCK.format(fake_id=fake_id))
            redis_client.delete(REDIS_VOICE_UID_FAKE_ID.format(user_id=user_id))

        # delete match infos
        if need_remove_from_pool:
            redis_client.delete(REDIS_VOICE_FAKE_START.format(fake_id=fake_id))
            other_fakeid = redis_client.get(REDIS_VOICE_MATCHED.format(fake_id=fake_id))
            if other_fakeid:
                redis_client.delete(REDIS_VOICE_FAKE_START.format(fake_id=other_fakeid))
                redis_client.delete(REDIS_VOICE_MATCHED.format(fake_id=fake_id))
                redis_client.delete(REDIS_VOICE_MATCHED.format(fake_id=other_fakeid))
                pair = low_high_pair(fake_id, other_fakeid)
                redis_client.delete(REDIS_VOICE_MATCH_PAIR.format(low_high_fakeid=pair))
                # redis_client.delete(REDIS_VOICE_FAKE_LIKE.format(fake_id=fake_id))
                # redis_client.delete(REDIS_VOICE_FAKE_LIKE.format(fake_id=other_fakeid))
            if not cls._remove_from_match_pool(BOY, fake_id):
                cls._remove_from_match_pool(GIRL, fake_id)
        redis_client.zrem(REDIS_VOICE_ANOY_CHECK_POOL, fake_id)

    @classmethod
    def _in_match(cls, fake_id1, fake_id2):
        pair = low_high_pair(fake_id1, fake_id2)
        in_match = redis_client.get(REDIS_VOICE_MATCH_PAIR.format(low_high_fakeid=pair))
        return True if in_match else False

    @classmethod
    def _create_match(cls, fake_id1, fake_id2, gender1):
        pair = low_high_pair(fake_id1, fake_id2)
        redis_client.set(REDIS_VOICE_MATCHED.format(fake_id=fake_id2), fake_id1, cls.MATCH_INT)
        redis_client.set(REDIS_VOICE_MATCHED.format(fake_id=fake_id1), fake_id2, cls.MATCH_INT)
        redis_client.set(REDIS_VOICE_MATCH_PAIR.format(low_high_fakeid=pair), 1, cls.MATCH_INT)
        redis_client.set(REDIS_VOICE_MATCHED_BEFORE.format(low_high_fakeid=pair), 1, ONE_DAY)

        # 将其从正在匹配队列中删除
        cls._remove_from_match_pool(gender1, fake_id1)
        cls._remove_from_match_pool(cls.OTHER_GENDER_M.get(gender1), fake_id2)

        cls._add_to_check_pool(fake_id1)
        cls._add_to_check_pool(fake_id2)
        return True

    @classmethod
    def _delete_match(cls, fake_id):
        fake_id2 = redis_client.get(REDIS_VOICE_MATCHED.format(fake_id=fake_id))
        if not fake_id2:
            cls._destroy_fake_id(fake_id, True)
            return True
        pair = low_high_pair(fake_id, fake_id2)
        redis_client.delete(REDIS_VOICE_MATCH_PAIR.format(low_high_fakeid=pair))
        cls._destroy_fake_id(fake_id, True)
        cls._destroy_fake_id(fake_id2, True)
        # map(cls._destroy_fake_id, [fake_id, fake_id2])
        return True

    @classmethod
    def _match(cls, fake_id, gender):
        '''
        return matched fake_id, if this match info has been set up
        '''
        matched_key = REDIS_VOICE_MATCHED.format(fake_id=fake_id)
        fake_id2 = redis_client.get(matched_key)
        if fake_id2:
            if cls._in_match(fake_id, fake_id2):
                # redis_client.delete(REDIS_VOICE_FAKE_START.format(fake_id=fake_id))
                return fake_id2, True
            redis_client.delete(matched_key)
        int_time = int(time.time())
        judge_time = int_time - cls.MATCH_WAIT
        other_gender = cls.OTHER_GENDER_M.get(gender)
        other_fakeids = redis_client.zrangebyscore(GlobalizationService.voice_match_key_by_region_gender(other_gender), judge_time, MAX_TIME, 0, cls.MAX_CHOOSE_NUM)
        if not other_fakeids:
            return None, False
        try_tms = 3
        for i in range(try_tms):
            fake_id2 = random.choice(other_fakeids)
            user_id2 = cls._uid_by_fake_id(fake_id2)
            user_id = cls._uid_by_fake_id(fake_id)
            if not redis_client.get(REDIS_VOICE_MATCHED_BEFORE.format(low_high_fakeid=low_high_pair(fake_id, fake_id2))):
                break
            elif i == try_tms - 1:
                return None,False
            # if not UserFilterService.filter_by_age_gender(user_id, user_id2) or not UserFilterService.filter_by_age_gender(user_id2, user_id):
            #     if i == try_tms - 1:
            #         return None, False
            #     continue
        # fake_id2 = random.choice(other_fakeids)
        # user_id = cls._uid_by_fake_id(fake_id)
        # user_id2 = cls._uid_by_fake_id(fake_id2)
        if BlockService.get_block_msg(user_id, user_id2):
            return None, False
        #redis_client.zadd(matched_key, {fake_id2: int_time})
        fake_id2_matched = redis_client.get(REDIS_VOICE_MATCHED.format(fake_id=fake_id2))
        if not fake_id2_matched or fake_id2_matched == fake_id:
            cls._create_match(fake_id, fake_id2, gender)
            return fake_id2, False
        return None, False

    @classmethod
    def _match_left_verify(cls, user_id):
        # 匹配次数验证
        now_date = now_date_key()
        match_left_key = REDIS_USER_VOICE_MATCH_LEFT.format(user_date=user_id + now_date)
        redis_client.setnx(match_left_key, cls.MATCH_TMS)
        redis_client.expire(match_left_key, ONE_DAY)
        times_left = int(redis_client.get(match_left_key))
        if times_left <= 0:
            return u'Your voicematch opportunity has run out, please try again tomorrow', False
        return times_left, True

    @classmethod
    def _decr_match_left(cls, user_id):
        now_date = now_date_key()
        match_left_key = REDIS_USER_VOICE_MATCH_LEFT.format(user_date=user_id + now_date)
        if not redis_client.get(match_left_key):
            redis_client.setnx(match_left_key, cls.MATCH_TMS)
            redis_client.expire(match_left_key, ONE_DAY)
        redis_client.decr(match_left_key)


    @classmethod
    def create_fakeid(cls, user_id):
        user = User.get_by_id(user_id)
        if not user:
            return USER_NOT_EXISTS, False

        gender = UserService.get_gender(user_id)
        if not gender:
            return PROFILE_NOT_COMPLETE, False
        user_id = str(user.id)
        msg, status = cls._match_left_verify(user_id)
        if not status:
            return msg, False
        old_fake_id = redis_client.get(REDIS_VOICE_UID_FAKE_ID.format(user_id=user_id))
        if old_fake_id:
            cls._destroy_fake_id(old_fake_id)

        fake_id, pwd = cls._get_voice_id(user)
        if not fake_id:
            return CREATE_HUANXIN_ERROR, False
        res = {
            'fake_id': fake_id,
            'password': pwd
        }
        # cls._add_to_check_pool(fake_id)
        # 建立fakeid:uid索引
        redis_client.set(REDIS_VOICE_FAKE_ID_UID.format(fake_id=fake_id), user_id, ex=cls.TOTAL_WAIT)

        # 建立uid:fakeid索引
        redis_client.set(REDIS_VOICE_UID_FAKE_ID.format(user_id=user_id), fake_id, ex=cls.TOTAL_WAIT)

        cls._add_to_match_pool(gender, fake_id)

        # 进入匹配过期
        redis_client.set(REDIS_VOICE_FAKE_START.format(fake_id=fake_id), 1, cls.MATCH_WAIT)
        return res, True

    @classmethod
    def voice_user_info(cls, fake_id):
        res = {}
        user_id = cls._uid_by_fake_id(fake_id)
        user = User.get_by_id(user_id)
        if not user_id:
            return res
        res['avatar'] = user.avatar
        return res

    @classmethod
    def anoy_match(cls, user_id):
        fake_id = cls._fakeid_by_uid(user_id)
        # 匹配已过期
        fake_expire_key = REDIS_VOICE_FAKE_START.format(fake_id=fake_id)
        if not fake_id or not redis_client.get(fake_expire_key):
            return u'fakeid: %s time out, please try another one' % fake_expire_key, False

        # msg = cls._match_left_verify(user_id)
        # if msg:
        #     return msg, False
        gender = UserService.get_gender(user_id)
        if not gender:
            return PROFILE_NOT_COMPLETE, False
        matched_id, has_matched = cls._match(fake_id, gender)
        if not matched_id:
            return u'please try again', False

        if not has_matched:
            # 减少今日剩余次数
            cls._decr_match_left(user_id)

            other_user_id = cls._uid_by_fake_id(matched_id)
            if other_user_id:
                cls._decr_match_left(other_user_id)
        tips, status = cls.get_tips()
        res = {
            'matched_fake_id': matched_id,
            'tips': tips
        }
        res.update(cls.voice_user_info(matched_id))
        return res, True

    @classmethod
    def get_times_left(cls, user_id):
        msg, status = cls._match_left_verify(user_id)
        times = 0
        if status:
            times = msg
        return {
            'wording': GlobalizationService.get_region_word('time_left') % times,
            'times': times
            }

    @classmethod
    def _uid_by_fake_id(cls, fake_id):
        return redis_client.get(REDIS_VOICE_FAKE_ID_UID.format(fake_id=fake_id))

    @classmethod
    def _fakeid_by_uid(cls, user_id):
        return redis_client.get(REDIS_VOICE_UID_FAKE_ID.format(user_id=user_id))

    @classmethod
    def _other_fakeid_byfake_id(cls, fake_id):
        return redis_client.get(REDIS_VOICE_MATCHED.format(fake_id=fake_id))

    @classmethod
    def anoy_like(cls, user_id):
        fake_id = cls._fakeid_by_uid(user_id)
        if not fake_id:
            return u'you have no match to quit', False
        other_fake_id = cls._other_fakeid_byfake_id(fake_id)
        if not other_fake_id or not cls._in_match(fake_id, other_fake_id):
            return u'your are not in match', False
        redis_client.set(REDIS_VOICE_FAKE_LIKE.format(fake_id=fake_id), other_fake_id, cls.MATCH_INT)
        like_eachother = False
        if redis_client.get(REDIS_VOICE_FAKE_LIKE.format(fake_id=other_fake_id)) == fake_id:
            like_eachother = True
            FollowService.follow_eachother(cls._uid_by_fake_id(fake_id), cls._uid_by_fake_id(other_fake_id))
        return {'like_eachother': like_eachother}, True

    @classmethod
    def clean_pools(cls):
        wait_buff = 2
        for g in GENDERS:
            from ..key import REDIS_ANOY_GENDER_ONLINE_REGION
            int_time = time.time()
            judge_time = int_time - cls.MATCH_WAIT
            for region in GlobalizationService.LOC_REGION.values():
                from flask import current_app,request, Flask
                app = Flask(__name__)
                from werkzeug.test import EnvironBuilder
                ctx = app.request_context(EnvironBuilder('/','http://localhost/').get_environ())
                ctx.push()
                request.region = region
                to_rem = redis_client.zrangebyscore(GlobalizationService.voice_match_key_by_region_gender(g), 0, judge_time - wait_buff, 0, cls.MAX_CHOOSE_NUM)
                for el in to_rem:
                    cls._destroy_fake_id(el)
                    print "match pool fake_id: %s destoryed" % el
                to_rem_check = redis_client.zrangebyscore(REDIS_VOICE_ANOY_CHECK_POOL.format(gender=g), 0,  int_time - cls.MATCH_INT - wait_buff, 0, cls.MAX_CHOOSE_NUM)
                for el in to_rem:
                    cls._destroy_fake_id(el, False)
                    print "check pool fake_id: %s destoryed" % el

    @classmethod
    def judge(cls, user_id, judge):
        fake_id = cls._fakeid_by_uid(user_id)
        other_fakeid = redis_client.get(REDIS_VOICE_MATCHED.format(fake_id=fake_id))
        if not other_fakeid:
            return NOT_IN_MATCH, False
        redis_key = REDIS_VOICE_JUDGE_LOCK.format(fake_id=fake_id)
        lock = redis_client.setnx(redis_key, 1)
        redis_client.expire(redis_key, cls.MATCH_INT)
        if not lock:
            return u'you have judged', False
        if not judge in User.JUDGES:
            return u'judge must be one of %s' % ','.join(User.JUDGES)
        other_user_id = cls._uid_by_fake_id(other_fakeid)
        user = User.get_by_id(other_user_id)
        user.add_judge(judge)
        return None, True


    @classmethod
    def quit_match(cls, user_id):   # should delete match pair
        fake_id = cls._fakeid_by_uid(user_id)
        if not fake_id:
            return None, True
            # return u'you have no match to quit', False
        # if cls._uid_by_fake_id(fake_id) != user_id:
        #     return u'you are not authorized to quit', False
        cls._delete_match(fake_id)
        return None, True
        # if possible to reset pwd

    @classmethod
    def debug_all_keys(cls, key=None):
        res = {'time_now': int(time.time())}
        for k in redis_client.keys():
            if key and key not in k:
                continue
            try:
                res[k] = redis_client.get(k)
            except:
                res[k] = redis_client.zscan(k)[1]
        return res
