# coding: utf-8
import time
import random
from ..redis import RedisClient
from ..key import (
    REDIS_USER_MATCH_LEFT,
    REDIS_FAKE_ID_UID,
    REDIS_FAKE_START,
    REDIS_ANOY_GENDER_ONLINE,
    REDIS_MATCH_PAIR,
    REDIS_MATCHED,
    REDIS_FAKE_LIKE
)
from ..util import (
    now_date_key,
    low_high_pair
)
from ..const import (
    ONLINE_LIVE,
    ONE_DAY,
    FIVE_MINS,
    BOY,
    GIRL,
    MAX_TIME,
    GENDERS,

    USER_NOT_EXISTS,
    PROFILE_NOT_COMPLETE
)
from ..service import (
    UserService,
    FollowService
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
        return user.huanxin.user_id

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
        redis_client.zrem(REDIS_ANOY_GENDER_ONLINE.format(gender=gender1), fake_id1)
        redis_client.zrem(REDIS_ANOY_GENDER_ONLINE.format(gender=cls.OTHER_GENDER_M.get(gender1)), fake_id2)

        return True

    @classmethod
    def _delete_match(cls, fake_id):
        user_id = cls._uid_by_fake_id(fake_id)
        if not user_id:
            return False
        fake_id2 = redis_client.get(REDIS_MATCHED.format(fake_id=fake_id))
        if not fake_id2:
            return False
        redis_client.delete(REDIS_FAKE_ID_UID.format(fake_id=fake_id))
        redis_client.delete(REDIS_FAKE_ID_UID.format(fake_id=fake_id2))
        pair = low_high_pair(fake_id, fake_id2)
        redis_client.delete(REDIS_MATCH_PAIR.format(low_high_fakeid=pair))
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
        other_fakeids = redis_client.zrangebyscore(REDIS_ANOY_GENDER_ONLINE.format(gender=other_gender), judge_time, 0, cls.MAX_CHOOSE_NUM)
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
    def anoy_match(cls, user_id, fake_id=None):
        user = User.get_by_id(user_id)
        if not user:
            return USER_NOT_EXISTS, False

        gender = UserService.get_gender(user_id)
        if not gender:
            return PROFILE_NOT_COMPLETE, False

        int_time = int(time.time())
        fake_expire_key = REDIS_FAKE_START.format(fake_id=fake_id)

        # 匹配次数验证
        now_date = now_date_key()
        key = REDIS_USER_MATCH_LEFT.format(user_date=user_id + now_date)
        redis_client.setnx(key, 10, ex=ONE_DAY)
        times_left = int(redis_client.get(key))
        if times_left <= 0:
            return u'Your anoymatch opportunity has run out, please try again tomorrow', False

        if not fake_id:
            fake_id = cls._get_anoy_id(user)

            # 建立fakeid:uid索引
            fake_uid_key = REDIS_FAKE_ID_UID.format(fake_id=fake_id)
            redis_client.set(fake_uid_key, user_id, ex=cls.TOTAL_WAIT)

            # 进入匹配id池子
            anoy_gender_key = REDIS_ANOY_GENDER_ONLINE.format(gender=gender)
            redis_client.zadd(anoy_gender_key,{fake_id: int_time} )

            # 进入匹配过期
            redis_client.set(fake_expire_key, 1, cls.MATCH_WAIT)

        # 匹配已过期
        if not redis_client.get(fake_expire_key):
            return u'time out, another try', False

        matched_id = cls._match(fake_id, gender)
        if not matched_id:
            return u'please try again', False

        # 减少今日剩余次数
        key = REDIS_USER_MATCH_LEFT.format(user_date=user_id + now_date)
        redis_client.decr(key)
        return matched_id, True

    @classmethod
    def _uid_by_fake_id(cls, fake_id):
        return redis_client.get(REDIS_FAKE_ID_UID.format(fake_id=fake_id))

    @classmethod
    def anoy_like(cls, fake_id, other_fake_id, user_id):
        if not cls._in_match(fake_id, other_fake_id):
            return u'your are not in match', False
        res = {}
        redis_client.set(REDIS_FAKE_LIKE.format(fake_id=fake_id), other_fake_id, cls.MATCH_INT)

        if redis_client.get(REDIS_FAKE_LIKE.format(fake_id=fake_id)) == fake_id:
            FollowService.follow(cls._uid_by_fake_id(fake_id), cls._uid_by_fake_id(other_fake_id))


    @classmethod
    def quit_match(cls, fake_id, user_id):   # should delete match pair
        if cls._uid_by_fake_id(fake_id) != user_id:
            return u'you are not authorized to quit', False
        cls._delete_match(fake_id)
        # if possible to reset pwd