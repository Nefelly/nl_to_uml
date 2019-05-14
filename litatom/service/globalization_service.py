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
    REDIS_ANOY_GENDER_ONLINE_REGION
)
from ..const import (
    ONLINE_LIVE
)
redis_client = RedisClient()['lit']

class GlobalizationService(object):
    '''
    https://blog.csdn.net/liuhhaiffeng/article/details/54706027
    '''
    REGIONS = {
        'TH',   # 泰国
        'IN',   # 印度
        'VN',   # 越南
        'ID'    # 印尼
    }
    LOC_REGION = {'TH': 'th', 'VN': 'vi', 'IN': 'india', 'ID': 'id'}
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
    def _set_loc_cache(cls, user_id, loc):
        loc_key = REDIS_USER_LOC.format(user_id=user_id)
        redis_client.set(loc_key, loc, ONLINE_LIVE)

    @classmethod
    def _set_user_loc(cls, user_id, loc):
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting:
            UserSetting.create_setting(user_id, loc)
        cls._set_loc_cache(user_id, loc)

    @classmethod
    def get_region(cls, region=None):
        loc = None
        if region:
            return region
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
        print loc
        if cls.LOC_REGION.get(loc, ''):
            return cls.LOC_REGION[loc]
        return 'th'

    @classmethod
    def change_loc(cls, user_id, target_loc):
        '''
        TODO: authorize, speed limitation and modify pool
        :param user_id:
        :param target_loc:
        :return:
        '''
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
