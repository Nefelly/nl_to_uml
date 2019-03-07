# coding: utf-8
import time
import random
from ..redis import RedisClient
from ..key import (
    REDIS_USER_MATCH_LEFT,
    REDIS_FAKE_ID_UID,
    REDIS_UID_FAKE_ID,
    REDIS_FAKE_START,
    REDIS_ANOY_GENDER_ONLINE,
    REDIS_ANOY_CHECK_POOL,
    REDIS_MATCH_PAIR,
    REDIS_MATCHED,
    REDIS_FAKE_LIKE
)
from ..util import (
    now_date_key,
    low_high_pair
)
from ..const import (
    CREATE_HUANXIN_ERROR,
    ONE_DAY,
    FIVE_MINS,
    BOY,
    GIRL,
    MAX_TIME,
    USER_NOT_EXISTS,
    PROFILE_NOT_COMPLETE
)
from ..service import (
    UserService,
    FollowService,
    HuanxinService
)
from ..model import User
redis_client = RedisClient()['lit']

class AnoyMatchService(object):
    MAX_TIME = 10 ** 13
    MATCH_WAIT = 60 * 3 + 1
    MATCH_INT = 60 * 3
    TOTAL_WAIT = MATCH_INT + MATCH_WAIT + FIVE_MINS
    MAX_CHOOSE_NUM = 10
    OTHER_GENDER_M = {BOY: GIRL, GIRL: BOY}

    @classmethod
    def _get_anoy_id(cls, user):
        return HuanxinService.gen_id_pwd()

    @classmethod
    def _add_to_match_pool(cls, gender, fake_id):
        # 进入匹配id池子
        if not gender or not fake_id:
            return
        int_time = int(time.time())
        anoy_gender_key = REDIS_ANOY_GENDER_ONLINE.format(gender=gender)
        redis_client.zadd(anoy_gender_key,{fake_id: int_time} )

    @classmethod
    def _remove_from_match_pool(cls, gender, fake_id):
        if not gender or not fake_id:
            return
        redis_client.zrem(REDIS_ANOY_GENDER_ONLINE.format(gender=gender), fake_id)

    @classmethod
    def _add_to_check_pool(cls, fake_id):
        if not fake_id:
            return
        int_time = int(time.time())
        redis_client.zadd(REDIS_ANOY_CHECK_POOL, {fake_id: int_time})

    @classmethod
    def _destroy_fake_id(cls, fake_id, need_remove_from_pool=True):
        if not fake_id:
            return
        HuanxinService.delete_user(fake_id)
        user_id = redis_client.get(REDIS_FAKE_ID_UID.format(fake_id=fake_id))
        redis_client.delete(REDIS_FAKE_START.format(fake_id=fake_id))
        if user_id:
            redis_client.delete(REDIS_FAKE_ID_UID.format(fake_id=fake_id))
            redis_client.delete(REDIS_UID_FAKE_ID.format(user_id=user_id))

        # delete match infos
        if need_remove_from_pool:
            other_fakeid = redis_client.get(REDIS_MATCHED.format(fake_id=fake_id))
            if other_fakeid:
                redis_client.delete(REDIS_MATCHED.format(fake_id=fake_id))
                redis_client.delete(REDIS_MATCHED.format(fake_id=other_fakeid))
                pair = low_high_pair(fake_id, other_fakeid)
                redis_client.delete(REDIS_MATCH_PAIR.format(low_high_fakeid=pair))
                # redis_client.delete(REDIS_FAKE_LIKE.format(fake_id=fake_id))
                # redis_client.delete(REDIS_FAKE_LIKE.format(fake_id=other_fakeid))
            if not cls._remove_from_match_pool(BOY, fake_id):
                cls._remove_from_match_pool(GIRL, fake_id)
        redis_client.zrem(REDIS_ANOY_CHECK_POOL, fake_id)

    @classmethod
    def _in_match(cls, fake_id1, fake_id2):
        pair = low_high_pair(fake_id1, fake_id2)
        in_match = redis_client.get(REDIS_MATCH_PAIR.format(low_high_fakeid=pair))
        return True if in_match else False

    @classmethod
    def _create_match(cls, fake_id1, fake_id2, gender1):
        pair = low_high_pair(fake_id1, fake_id2)
        redis_client.set(REDIS_MATCHED.format(fake_id=fake_id2), fake_id1, cls.MATCH_INT)
        redis_client.set(REDIS_MATCHED.format(fake_id=fake_id1), fake_id2, cls.MATCH_INT)
        redis_client.set(REDIS_MATCH_PAIR.format(low_high_fakeid=pair), 1, cls.MATCH_INT)

        # 将其从正在匹配队列中删除
        cls._remove_from_match_pool(gender1, fake_id1)
        cls._remove_from_match_pool(cls.OTHER_GENDER_M.get(gender1), fake_id2)
        return True

    @classmethod
    def _delete_match(cls, fake_id):
        fake_id2 = redis_client.get(REDIS_MATCHED.format(fake_id=fake_id))
        pair = low_high_pair(fake_id, fake_id2)
        redis_client.delete(REDIS_MATCH_PAIR.format(low_high_fakeid=pair))
        cls._destroy_fake_id(fake_id, False)
        cls._destroy_fake_id(fake_id2, False)
        # map(cls._destroy_fake_id, [fake_id, fake_id2])
        return True

    @classmethod
    def _match(cls, fake_id, gender):
        matched_key = REDIS_MATCHED.format(fake_id=fake_id)
        fake_id2 = redis_client.get(matched_key)
        if fake_id2:
            if cls._in_match(fake_id, fake_id2):
                return fake_id2
            redis_client.delete(matched_key)
        int_time = int(time.time())
        judge_time = int_time - cls.MATCH_WAIT
        other_gender = cls.OTHER_GENDER_M.get(gender)
        other_fakeids = redis_client.zrangebyscore(REDIS_ANOY_GENDER_ONLINE.format(gender=other_gender), judge_time, 0, MAX_TIME, cls.MAX_CHOOSE_NUM)
        if not other_fakeids:
            return None
        fake_id2 = random.choice(other_fakeids)
        redis_client.zadd(matched_key, {fake_id2: int_time})
        fake_id2_matched = redis_client.get(REDIS_MATCHED.format(fake_id=fake_id2))
        if not fake_id2_matched or fake_id2_matched == fake_id:
            cls._create_match(fake_id, fake_id2, gender)
            return fake_id2
        return None

    @classmethod
    def _match_left_verify(cls, user_id):
        # 匹配次数验证
        now_date = now_date_key()
        match_left_key = REDIS_USER_MATCH_LEFT.format(user_date=user_id + now_date)
        redis_client.setnx(match_left_key, 10)
        redis_client.expire(match_left_key, ONE_DAY)
        times_left = int(redis_client.get(match_left_key))
        if times_left <= 0:
            return u'Your anoymatch opportunity has run out, please try again tomorrow'
        return None

    @classmethod
    def create_fakeid(cls, user_id):
        user = User.get_by_id(user_id)
        if not user:
            return USER_NOT_EXISTS, False

        gender = UserService.get_gender(user_id)
        if not gender:
            return PROFILE_NOT_COMPLETE, False
        user_id = str(user.id)
        msg = cls._match_left_verify(user_id)
        if msg:
            return msg, False
        old_fake_id = redis_client.get(REDIS_UID_FAKE_ID.format(user_id=user_id))
        if old_fake_id:
            cls._destroy_fake_id(old_fake_id)
        fake_id, pwd = cls._get_anoy_id(user)
        if not fake_id:
            return CREATE_HUANXIN_ERROR, False
        res = {
            'fake_id': fake_id,
            'password': pwd
        }
        # 建立fakeid:uid索引
        redis_client.set(REDIS_FAKE_ID_UID.format(fake_id=fake_id), user_id, ex=cls.TOTAL_WAIT)

        # 建立uid:fakeid索引
        redis_client.set(REDIS_UID_FAKE_ID.format(user_id=user_id), fake_id, ex=cls.TOTAL_WAIT)

        cls._add_to_match_pool(gender, fake_id)

        # 进入匹配过期
        redis_client.set(REDIS_FAKE_START.format(fake_id=fake_id), 1, cls.MATCH_WAIT)
        return res, True

    @classmethod
    def anoy_match(cls, user_id, fake_id):
        # 匹配已过期
        fake_expire_key = REDIS_FAKE_START.format(fake_id=fake_id)
        if not fake_id or not redis_client.get(fake_expire_key):
            return u'fakeid: %s time out, please try another one' % fake_expire_key, False

        # msg = cls._match_left_verify(user_id)
        # if msg:
        #     return msg, False
        gender = UserService.get_gender(user_id)
        if not gender:
            return PROFILE_NOT_COMPLETE, False
        matched_id = cls._match(fake_id, gender)
        if not matched_id:
            return u'please try again', False

        # 减少今日剩余次数
        now_date = now_date_key()
        key = REDIS_USER_MATCH_LEFT.format(user_date=user_id + now_date)
        redis_client.decr(key)
        res = {'matched_fake_id': fake_id}
        return res, True

    @classmethod
    def _uid_by_fake_id(cls, fake_id):
        return redis_client.get(REDIS_FAKE_ID_UID.format(fake_id=fake_id))

    @classmethod
    def anoy_like(cls, fake_id, other_fake_id, user_id):
        if not cls._in_match(fake_id, other_fake_id):
            return u'your are not in match', False
        redis_client.set(REDIS_FAKE_LIKE.format(fake_id=fake_id), other_fake_id, cls.MATCH_INT)
        like_eachother = False
        if redis_client.get(REDIS_FAKE_LIKE.format(fake_id=fake_id)) == fake_id:
            like_eachother = True
            FollowService.follow_eachother(cls._uid_by_fake_id(fake_id), cls._uid_by_fake_id(other_fake_id))
        return {'like_eachother': like_eachother}, True


    @classmethod
    def quit_match(cls, fake_id, user_id):   # should delete match pair
        if cls._uid_by_fake_id(fake_id) != user_id:
            return u'you are not authorized to quit', False
        cls._delete_match(fake_id)
        # if possible to reset pwd