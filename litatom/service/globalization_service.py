# coding: utf-8
import time
from flask import (
    request
)
from ..redis import RedisClient
from ..model import (
    RegionWord,
    UserSetting,
    User
)

from ..key import (
    REDIS_REGION_TAG_WORD,
    REDIS_USER_LOC,
    REDIS_ONLINE_GENDER,
    REDIS_ONLINE_GENDER_REGION,
    REDIS_ONLINE,
    REDIS_ONLINE_REGION,
    REDIS_ANOY_GENDER_ONLINE_REGION,
    REDIS_VOICE_GENDER_ONLINE_REGION,
    REDIS_VIDEO_GENDER_ONLINE_REGION
)
from ..const import (
    ONLINE_LIVE,
    GENDERS
)
from ..service import (
    Ip2AddressService
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
    REGION_IN_NOCORE = 'indiaNoCore'
    REGION_KR = 'ko'


    LOC_TH = 'TH'   # 泰国
    LOC_IN = 'IN'   # 印度
    LOC_VN = 'VN'   # 越南
    LOC_ID = 'ID'   # 印尼
    LOC_CN = 'CN'   # 中国
    LOC_TE = 'TEST' # 测试,混杂区
    LOC_TH2 = 'th'
    LOC_INN = 'INN'
    LOC_KR = 'KR'

    LOCS = {
        LOC_TH,
        LOC_IN,
        LOC_VN,
        LOC_ID,
        LOC_CN,
        LOC_TE,
        LOC_INN,
        LOC_KR
    }

    KOWN_REGION_LOC = {
        REGION_VN: LOC_VN,
        REGION_TH: [LOC_TH, LOC_CN, LOC_TH2],
        REGION_ID: LOC_ID,
        REGION_IN: LOC_IN,
        REGION_KR: LOC_KR
    }

    COUNTRY_LOC = {
        'Indonesia': LOC_ID,
        'Thailand': LOC_TH,
        'Vietnam': LOC_VN,
        'China': LOC_CN,
        'India': LOC_IN,
        'South Korea': LOC_KR
    }


    # LOCS = {
    #     'TH',
    #     'IN',
    #     'VN',   # 越南
    #     'ID'    # 印尼
    # }

    DEFAULT_REGION  = REGION_EN

    LOC_REGION = {
        'TH': REGION_TH,
        'VN': REGION_VN,
        'IN': REGION_IN,
        'ID': REGION_ID,
        'th': REGION_TH,
        'CN': REGION_TH,
        'INN': REGION_IN_NOCORE
    }
    REGIONS = list(set(LOC_REGION.values()))
    REGIONS.append(REGION_EN)
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
    def region_by_loc(cls, loc):
        return cls.LOC_REGION.get(loc, cls.REGION_EN)

    @classmethod
    def get_real_loc(cls, loc):
        if loc in cls.LOCS:
            if loc == cls.LOC_IN:
                return loc
            return loc
        return cls.COUNTRY_LOC.get(request.ip_country, loc)

    @classmethod
    def anoy_match_key_by_region_gender(cls, gender):
        region = cls.get_region()
        return REDIS_ANOY_GENDER_ONLINE_REGION.format(region=region, gender=gender)

    @classmethod
    def voice_match_key_by_region_gender(cls, gender):
        region = cls.get_region()
        return REDIS_VOICE_GENDER_ONLINE_REGION.format(region=region, gender=gender)


    @classmethod
    def video_match_key_by_region_gender(cls, gender):
        region = cls.get_region()
        return REDIS_VIDEO_GENDER_ONLINE_REGION.format(region=region, gender=gender)

    @classmethod
    def set_current_region_for_script(cls, region):
        from flask import current_app,request, Flask
        app = Flask(__name__)
        from werkzeug.test import EnvironBuilder
        ctx = app.request_context(EnvironBuilder('/','http://localhost/').get_environ())
        ctx.push()
        request.region = region

    @classmethod
    def rem_from_region(cls, user_id, region):
        cls.set_current_region_for_script(region)
        for g in GENDERS + [None]:
            key = GlobalizationService._online_key_by_region_gender(g)
            redis_client.zrem(key, user_id)
        from ..model import Feed
        keys = []
        from ..key import REDIS_FEED_HQ_REGION, REDIS_FEED_SQUARE_REGION
        keys.append(REDIS_FEED_HQ_REGION.format(region=region))
        keys.append(REDIS_FEED_SQUARE_REGION.format(region=region))
        feedids = [str(el.id) for el in Feed.get_by_user_id(user_id)]
        for _ in keys:
            for el in feedids:
                redis_client.zrem(_, el)

    @classmethod
    def _set_loc_cache(cls, user_id, loc):
        loc_key = REDIS_USER_LOC.format(user_id=user_id)
        old_loc = redis_client.get(REDIS_USER_LOC.format(user_id=user_id))
        if old_loc and old_loc != loc:
            cls._purge_loc_cache(user_id, old_loc)
        redis_client.set(loc_key, loc, ONLINE_LIVE)

    @classmethod
    def _set_user_loc(cls, user_id, loc):
        user_setting = UserSetting.get_by_user_id(user_id)
        if loc == 'th':
            loc = 'TH'
        if not user_setting:
            UserSetting.create_setting(user_id, loc)
        else:
            if user_setting.lang != loc and user_setting.lang in cls.LOCS:   #
                return False
        cls._set_loc_cache(user_id, loc)
        return True

    @classmethod
    def _purge_loc_cache(cls, user_id, loc):
        request.region = cls.region_by_loc(loc)
        if request.region:
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
            if not tmp_loc:
                user_setting =  UserSetting.get_by_user_id(user_id)
                if user_setting and user_setting.lang and user_setting.lang in cls.LOCS:
                    tmp_loc = user_setting.lang
            if tmp_loc and tmp_loc in cls.LOCS:
                loc = tmp_loc
            else:
                cls._set_user_loc(user_id, request.loc)
                loc = request.loc
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
        if target_loc not in cls.LOCS:
            return u'your loc must be in one of [%s]' % (','.join(cls.LOCS)), False
        UserSetting.ensure_setting(user_id, target_loc)
        cls._set_loc_cache(user_id, target_loc)
        return  None, True

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
        # word = redis_client.get(cls._region_tag_key(region, tag))
        word = ''
        if region == cls.REGION_IN or region == cls.REGION_IN_NOCORE:
            region = cls.REGION_EN
        if not word:
            word = RegionWord.word_by_region_tag(region, tag)
            # if word:
            #     redis_client.set(cls._region_tag_key(region, tag), word)
        return word


