# coding: utf-8
import time
from flask import (
    request
)
from ..redis import RedisClient
from ..model import (
    RegionWord,
    UserSetting
)

from ..key import (
    REDIS_REGION_TAG_WORD,
    REDIS_USER_LOC,
    REDIS_ONLINE_GENDER,
    REDIS_ONLINE_GENDER_REGION,
    REDIS_ONLINE,
    REDIS_ONLINE_REGION,
    REDIS_ANOY_GENDER_ONLINE_REGION,
    REDIS_VOICE_GENDER_ONLINE_REGION
)
from ..const import (
    ONLINE_LIVE,
    GENDERS
)
redis_client = RedisClient()['lit']

class GlobalizationService(object):
    '''
    https://blog.csdn.net/liuhhaiffeng/article/details/54706027
    '''
    REGION_TH = 'th'
    REGION_IN = 'india'
    REGION_ID = 'id'
    REGION_VN = 'vi'
    REGION_EN = 'en'
    REGIONS = {
        'TH',   # 泰国
        'IN',   # 印度
        'VN',   # 越南
        'ID'    # 印尼
    }
    DEFAULT_REGION  = 'th'
    LOC_REGION = {'TH': REGION_TH, 'VN': REGION_VN, 'IN': REGION_IN, 'ID': REGION_ID, 'th': REGION_TH, 'CN': REGION_TH}
    '''
    todo: user loc set in redis
    '''
    @classmethod
    def _online_key_by_region_gender(cls, gender=None):
        region = cls.get_region()
        if gender:
            return REDIS_ONLINE_GENDER_REGION.format(region=region, gender=gender)
        else:
            return REDIS_ONLINE_REGION.format(region=region)

    @classmethod
    def anoy_match_key_by_region_gender(cls, gender):
        region = cls.get_region()
        return REDIS_ANOY_GENDER_ONLINE_REGION.format(region=region, gender=gender)

    @classmethod
    def voice_match_key_by_region_gender(cls, gender):
        region = cls.get_region()
        return REDIS_VOICE_GENDER_ONLINE_REGION.format(region=region, gender=gender)

    @classmethod
    def _set_loc_cache(cls, user_id, loc):
        loc_key = REDIS_USER_LOC.format(user_id=user_id)
        old_loc = redis_client.get(REDIS_USER_LOC.format(user_id=user_id))
        if old_loc:
            cls._purge_loc_cache(user_id, old_loc)
        redis_client.set(loc_key, loc, ONLINE_LIVE)

    @classmethod
    def _set_user_loc(cls, user_id, loc):
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting:
            UserSetting.create_setting(user_id, loc)
        cls._set_loc_cache(user_id, loc)

    @classmethod
    def _purge_loc_cache(cls, user_id, loc):
        for g in GENDERS + [None]:
            key = GlobalizationService._online_key_by_region_gender(g)
            redis_client.zrem(key, user_id)
        loc_key = REDIS_USER_LOC.format(user_id=user_id)
        redis_client.delete(loc_key)   # delete old loc_key
        return True

    @classmethod
    def get_region(cls, region=None):
        if region:
            return region
        if getattr(request, 'region', ''):
            return request.region
        loc = None
        user_id = request.user_id
        if user_id:
            loc_key = REDIS_USER_LOC.format(user_id=user_id)
            tmp_loc = redis_client.get(loc_key)
            if tmp_loc:
                loc = tmp_loc
            else:
                cls._set_user_loc(user_id, request.loc)
        else:
            loc = request.loc
        if cls.LOC_REGION.get(loc, ''):
            res = cls.LOC_REGION[loc]
        else:
            res = cls.DEFAULT_REGION
        request.region = res
        return res

    @classmethod
    def change_loc(cls, user_id, target_loc):
        '''
        TODO: authorize, speed limitation and modify pool
        :param user_id:
        :param target_loc:
        :return:
        '''
        if target_loc not in cls.REGIONS:
            return u'your loc must be in one of [%s]' % (','.join(cls.REGIONS)), False
        UserSetting.ensure_setting(user_id, target_loc)
        cls._set_loc_cache(user_id, target_loc)
        return True, None

    @classmethod
    def _region_tag_key(cls, region, tag):
        region_tag = '%s:%s' % (region, tag)
        return REDIS_REGION_TAG_WORD.format(region_tag=region_tag)

    @classmethod
    def add_or_modify_region_words(cls, region, tag, word):
        if RegionWord.add_or_mod(region, tag, word):
            redis_client.set(cls._region_tag_key(region, tag), word)
        return True

    @classmethod
    def get_region_word(cls, tag, region=None):
        if not region:
            region = cls.get_region()
        word = redis_client.get(cls._region_tag_key(region, tag))
        if not word:
            word = RegionWord.word_by_region_tag(region, tag)
            if word:
                redis_client.set(cls._region_tag_key(region, tag), word)
        return word
