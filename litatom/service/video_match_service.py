# coding: utf-8
import time
import datetime
import random
from hendrix.conf import setting
from ..redis import RedisClient
from ..key import (
    REDIS_USER_VIDEO_MATCH_LEFT,
    REDIS_VIDEO_FAKE_ID_UID,
    REDIS_VIDEO_UID_FAKE_ID,
    REDIS_VIDEO_FAKE_START,
    REDIS_VIDEO_ANOY_CHECK_POOL,
    REDIS_VIDEO_MATCH_PAIR,
    REDIS_VIDEO_MATCHED_BEFORE,
    REDIS_VIDEO_MATCHED,
    REDIS_VIDEO_FAKE_LIKE,
    REDIS_VIDEO_JUDGE_LOCK,
    REDIS_VIDEO_VID
)
from ..util import (
    low_high_pair
)
from ..const import (
    FIVE_MINS,
    BOY,
    GIRL,
    ALL_FILTER
)
from ..service import (
    GlobalizationService,
    MatchService
)
from ..model import (
    YoutubeVideo
)
redis_client = RedisClient()['lit']

class VideoMatchService(MatchService):
    MATCH_WAIT = 60 * 7 + 1
    MATCH_INT = 60 * 7  # talking time
    TOTAL_WAIT = MATCH_INT + MATCH_WAIT + FIVE_MINS
    MAX_CHOOSE_NUM = 100
    MATCH_TMS = 20 if not setting.IS_DEV else 1000

    TYPE_ANOY_CHECK_POOL = REDIS_VIDEO_ANOY_CHECK_POOL
    TYPE_FAKE_ID_UID = REDIS_VIDEO_FAKE_ID_UID
    TYPE_UID_FAKE_ID = REDIS_VIDEO_UID_FAKE_ID
    TYPE_FAKE_START = REDIS_VIDEO_FAKE_START
    TYPE_MATCHED = REDIS_VIDEO_MATCHED
    TYPE_MATCH_BEFORE = REDIS_VIDEO_MATCHED_BEFORE
    TYPE_ANOY_CHECK_POOL = REDIS_VIDEO_ANOY_CHECK_POOL
    TYPE_USER_MATCH_LEFT = REDIS_USER_VIDEO_MATCH_LEFT
    TYPE_FAKE_LIKE = REDIS_VIDEO_FAKE_LIKE
    TYPE_MATCH_PAIR = REDIS_VIDEO_MATCH_PAIR
    TYPE_JUDGE_LOCK = REDIS_VIDEO_JUDGE_LOCK
    MATCH_TYPE = 'video'
    if not ALL_FILTER:
        MATCH_KEY_BY_REGION_GENDER = GlobalizationService.video_match_key_by_region_gender

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
    def _random_choose_video(cls):
        vlist = GlobalizationService.get_region_word('video_list')
        return random.choice(vlist)

    @classmethod
    def _create_match(cls, fake_id1, fake_id2, gender1, user_id, user_id2):
        status = super(VideoMatchService, cls)._create_match(fake_id1, fake_id2, gender1, user_id, user_id2)
        if not status:
            return False
        pair = low_high_pair(fake_id1, fake_id2)
        redis_client.set(REDIS_VIDEO_VID.format(low_high_fakeid=pair), cls._random_choose_video(), cls.MATCH_INT)
        return True

    @classmethod
    def anoy_match(cls, user_id):
        res, status = super(VideoMatchService, cls).anoy_match(user_id)
        if not status:
            return res, status
        fake_id = cls._fakeid_by_uid(user_id)
        matched_id = res.get('matched_fake_id')
        res.update(
            {
                'video': redis_client.get(REDIS_VIDEO_VID.format(low_high_fakeid=low_high_pair(fake_id, matched_id))),
                'video_info': YoutubeVideo.info_by_vid(
                    redis_client.get(REDIS_VIDEO_VID.format(low_high_fakeid=low_high_pair(fake_id, matched_id))))
            }
        )
        return res, True
