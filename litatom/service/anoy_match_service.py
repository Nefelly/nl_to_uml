# coding=utf-8
from hendrix.conf import setting
from ..key import (
    REDIS_USER_MATCH_LEFT,
    REDIS_FAKE_ID_UID,
    REDIS_UID_FAKE_ID,
    REDIS_FAKE_START,
    REDIS_ANOY_CHECK_POOL,
    REDIS_MATCH_BEFORE,
    REDIS_MATCHED,
    REDIS_FAKE_LIKE,
    REDIS_MATCH_PAIR,
    REDIS_JUDGE_LOCK
)
from ..const import (
    FIVE_MINS,
    BOY,
    GIRL,
)
from ..service import (
    GlobalizationService,
    MatchService
)

class AnoyMatchService(MatchService):
    MATCH_WAIT = 60 * 3 + 1
    MATCH_INT = 60 * 3  # talking time
    MAX_CHOOSE_NUM = 40
    TOTAL_WAIT = MATCH_INT + MATCH_WAIT + FIVE_MINS
    MATCH_TMS = 20 if not setting.IS_DEV else 1000

    TYPE_ANOY_CHECK_POOL = REDIS_ANOY_CHECK_POOL
    TYPE_FAKE_ID_UID = REDIS_FAKE_ID_UID
    TYPE_UID_FAKE_ID = REDIS_UID_FAKE_ID
    TYPE_FAKE_START = REDIS_FAKE_START
    TYPE_MATCHED = REDIS_MATCHED
    TYPE_MATCH_BEFORE = REDIS_MATCH_BEFORE
    TYPE_ANOY_CHECK_POOL = REDIS_ANOY_CHECK_POOL
    TYPE_USER_MATCH_LEFT = REDIS_USER_MATCH_LEFT
    TYPE_FAKE_LIKE = REDIS_FAKE_LIKE
    TYPE_MATCH_PAIR = REDIS_MATCH_PAIR
    TYPE_JUDGE_LOCK = REDIS_JUDGE_LOCK
    MATCH_TYPE = 'soul'
    MATCH_KEY_BY_REGION_GENDER = GlobalizationService.anoy_match_key_by_region_gender

    @classmethod
    def get_tips(cls):
        word = GlobalizationService.get_region_word('anoy_match_msg')
        data = {
            'chat_time': cls.MATCH_INT,
            BOY: [word],
            GIRL: [word]
        }
        return data, True
