# coding: utf-8
import time
import datetime
import random
from hendrix.conf import setting
from ..redis import RedisClient
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
from ..const import (
    FIVE_MINS,
    BOY,
    GIRL
)
from ..service import (
    GlobalizationService,
    MatchService
)
redis_client = RedisClient()['lit']

class VoiceMatchService(MatchService):
    MATCH_WAIT = 60 * 7 + 1
    MATCH_INT = 60 * 7  # talking time
    TOTAL_WAIT = MATCH_INT + MATCH_WAIT + FIVE_MINS
    MAX_CHOOSE_NUM = 100
    MATCH_TMS = 20 if not setting.IS_DEV else 1000

    TYPE_ANOY_CHECK_POOL = REDIS_VOICE_ANOY_CHECK_POOL
    TYPE_FAKE_ID_UID = REDIS_VOICE_FAKE_ID_UID
    TYPE_UID_FAKE_ID = REDIS_VOICE_UID_FAKE_ID
    TYPE_FAKE_START = REDIS_VOICE_FAKE_START
    TYPE_MATCHED = REDIS_VOICE_MATCHED
    TYPE_MATCH_BEFORE = REDIS_VOICE_MATCHED_BEFORE
    TYPE_ANOY_CHECK_POOL = REDIS_VOICE_ANOY_CHECK_POOL
    TYPE_USER_MATCH_LEFT = REDIS_USER_VOICE_MATCH_LEFT
    TYPE_FAKE_LIKE = REDIS_VOICE_FAKE_LIKE
    TYPE_MATCH_PAIR = REDIS_VOICE_MATCH_PAIR
    TYPE_JUDGE_LOCK = REDIS_VOICE_JUDGE_LOCK
    MATCH_KEY_BY_REGION_GENDER = GlobalizationService.voice_match_key_by_region_gender

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
