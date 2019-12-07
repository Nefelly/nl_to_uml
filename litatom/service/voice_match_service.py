# coding: utf-8
import time
import datetime
import random
from hendrix.conf import setting
from  flask import (
    request
)
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
    REDIS_VOICE_JUDGE_LOCK,
    REDIS_VOICE_SDK_TYPE
)
from ..const import (
    FIVE_MINS,
    BOY,
    GIRL,
    TYPE_VOICE_TENCENT,
    TYPE_VOICE_AGORA
)
from ..service import (
    GlobalizationService,
    MatchService,
    VoiceChatService
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
    MATCH_TYPE = 'voice'
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

    @classmethod
    def create_fakeid(cls, user_id):
        res, status = super(VoiceMatchService, cls).create_fakeid(user_id)
        if not status:
            return res, status
        voice_type = request.args.get('voice_type', None)
        if voice_type:
            redis_client.set(REDIS_VOICE_SDK_TYPE.format(user_id=user_id), voice_type, ex=cls.TOTAL_WAIT)
        return res, status

    @classmethod
    def anoy_match(cls, user_id):
        res, status = super(VoiceMatchService, cls).anoy_match(user_id)
        if not status:
            return res, status
        voice_type = TYPE_VOICE_AGORA
        matched_id = res.get('matched_fake_id')
        if redis_client.get(REDIS_VOICE_SDK_TYPE.format(user_id=user_id)) == TYPE_VOICE_TENCENT:
            other_user_id = cls._uid_by_fake_id(matched_id)
            if redis_client.get(REDIS_VOICE_SDK_TYPE.format(user_id=other_user_id)) == TYPE_VOICE_TENCENT:
                voice_type = TYPE_VOICE_TENCENT
        room_id, status = VoiceChatService.get_roomid(matched_id, cls._fakeid_by_uid(user_id))
        res.update(
            {
                'voice_type': voice_type,
                'room_id': room_id
            }
        )
        return res, True

    @classmethod
    def _destroy_fake_id(cls, fake_id, need_remove_from_pool=True):
        super(VoiceMatchService, cls)._destroy_fake_id(fake_id, need_remove_from_pool)
        if not fake_id:
            return
        user_id = redis_client.get(cls.TYPE_FAKE_ID_UID.format(fake_id=fake_id))
        if user_id:
            redis_client.delete(REDIS_VOICE_SDK_TYPE.format(user_id=user_id))
