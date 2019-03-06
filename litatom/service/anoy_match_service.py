# coding: utf-8
from ..redis import RedisClient
from ..key import (
    REDIS_USER_MATCH_LEFT,
    REDIS_FAKE_ID_UID,
    REDIS_FAKE_START,
    REDIS_ANOY_GENDER_ONLINE
)
from ..util import (
    now_date_key
)
from ..const import (
    ONLINE_LIVE,
    ONE_DAY,
    FIVE_MINS,
    GENDERS,
    USER_NOT_EXISTS,
    PROFILE_NOT_COMPLETE
)
from ..service import UserService
from ..model import User
redis_client = RedisClient()['lit']

class AnoyMatchService(object):
    MAX_TIME = 10 ** 13
    MATCH_WAIT = 60 * 3 + 1
    MATCH_INT = 60 * 3
    TOTAL_WAIT = MATCH_INT + MATCH_WAIT + FIVE_MINS
    @classmethod
    def _get_anoy_id(cls, user):
        return user.huanxin.user_id

    @classmethod
    def anoy_match(cls, user_id, fake_id=None):
        user = User.get_by_id(user_id)
        if not user:
            return USER_NOT_EXISTS, False
        if not fake_id:
            fake_id = cls._get_anoy_id(user)
            now_date = now_date_key()
            key = REDIS_USER_MATCH_LEFT.format(user_date=user_id + now_date)
            redis_client.setnx(key, 10, ex=ONE_DAY)
            times_left = int(redis_client.get(key))
            if times_left <= 0:
                return u'Your anoymatch opportunity has run out, please try again tomorrow', False
            fake_uid_key = REDIS_FAKE_ID_UID.format(fake_id=fake_id)
            redis_client.set(fake_uid_key, user_id, ex=cls.TOTAL_WAIT)

            gender = UserService.get_gender(user_id)
            if not gender:
                return PROFILE_NOT_COMPLETE, False
            anoy_gender_key = REDIS_ANOY_GENDER_ONLINE.format(gender=gender)
            redis_client.zadd(anoy_gender_key, fake_id, )

            in_match_key = REDIS_FAKE_START.format(fake_id=fake_id)
            redis_client.set(in_match_key, 1, cls.MATCH_WAIT)

