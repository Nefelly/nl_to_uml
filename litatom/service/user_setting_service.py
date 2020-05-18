# coding: utf-8
import time
import json
import copy
from flask import (
    request
)
from hendrix.conf import setting
from ..util import date_to_int_time
from ..model import (
    User,
    UserSetting,
    Uuids
)
from ..redis import RedisClient
from ..const import (
    ONE_HOUR,
    TYPE_VOICE_AGORA,
    TYPE_VOICE_TENCENT,
    PLATFORM_IOS
)
from ..key import (
    REDIS_SETTINGS_KEYS,
    REDIS_SETTINGS_IOS,
    REDIS_SETTINGS_IOS_VERSION
)

from ..service import (
    GlobalizationService,
    ExperimentService
)

redis_client = RedisClient()['lit']


class UserSettingService(object):
    DEFAULT_SETTING = {
            'need_login': True,
            'max_voice_time': ONE_HOUR,
            'pop_good_rate': True,
            'prior_voice': TYPE_VOICE_TENCENT,   # agora 声网，
            'phone_login_without_code': True,
            'modules_open': {
                "soul_match": 1,
                "video_match": 1,
                "voice_match": 1
            },
            'ad_rule': {
                'interval': 5,
                'adSupport23': False,
                'using_hamburger': True,
                'using_banner_hamburger': True,
                'disableGooglePlayCheck': True,
                'prior_platform': 'facebook', # facebook
                'need_ad': True,
                'banner_ad_type': 1,   # 1：nactive_ad, 2: banner_ad, 3: banner_native_ad
                'voice_match_top': True,
                'in_match': False,
                'im': True,
                'home_list': True,
                'user_feed': True,
                'user_feed_ad_type': 1,
                'need_916_ad': True,
                'chat_list': True,
                'anti_spam_rule': {
                    "times": 5,
                    "time_interval": 60,
                    "spam_interval": 60 * 2
                }
            },
            'show_accelerate': False,
            'upload_network_err': False
        }

    @classmethod
    def get_setting_key(cls):
        if request.platform != PLATFORM_IOS:
            return REDIS_SETTINGS_KEYS
        if request.version and request.version > '1.2.3':
            return REDIS_SETTINGS_IOS_VERSION.format(version=request.version)
        return REDIS_SETTINGS_IOS

    @classmethod
    def change_setting(cls, data):
        setting_string = json.dumps(data)
        if not cls._valid_cache_str(setting_string):
            return 'Not valid setting', False
        redis_client.set(cls.get_setting_key(), setting_string)
        return None, True

    @classmethod
    def _valid_cache_str(cls, cached_setting_str):
        res = cls.DEFAULT_SETTING
        if not cached_setting_str:
            return False
        else:
            cached_setting = json.loads(cached_setting_str)
            if len(cached_setting.keys()) < len(res.keys()):
                return False
            else:
                for key in cached_setting:
                    if isinstance(cached_setting[key], dict):
                        if len(cached_setting[key].keys()) < len(res[key].keys()):
                            return False
        return True

    @classmethod
    def get_settings(cls, user_id=None):
        if not user_id and request.uuid:
            Uuids.create(request.uuid, request.loc)
        res = copy.deepcopy(cls.DEFAULT_SETTING)
        # need_pop = False
        # if user_id:
        #     userSetting = UserSetting.get_by_user_id(user_id)
        #     if userSetting:
        #         pop_time_interval = [0.5 * ONE_DAY, 2 * ONE_DAY, 10 * ONE_DAY]
        #         create_ts = date_to_int_time(userSetting.create_time)
        #         if len(pop_time_interval) > userSetting.good_rate_times and int(time.time()) - create_ts > pop_time_interval[userSetting.good_rate_times]:
        #             need_pop = True
        #             userSetting.good_rate_times += 1
        #             userSetting.save()
        # res['pop_good_rate'] = need_pop

        region = GlobalizationService.get_region()
        if setting.IS_DEV or 1:
            cached_setting_str = redis_client.get(cls.get_setting_key())
            if False and not cls._valid_cache_str(cached_setting_str):
                redis_client.delete(cls.get_setting_key())
                redis_client.set(cls.get_setting_key(), json.dumps(res))
            else:
                tmp_res = json.loads(cached_setting_str)
                if tmp_res:
                    res = tmp_res
        # print region, "!" * 100, region not in [GlobalizationService.REGION_TH]
        if region not in [GlobalizationService.REGION_TH, GlobalizationService.REGION_VN]:
               res['modules_open']['video_match'] = 0
        if region == GlobalizationService.REGION_ID:
            if ExperimentService.get_exp_value('id_show_video') == 'show':
                res['modules_open']['video_match'] = 1
        if region == GlobalizationService.REGION_PH:
            res['modules_open']['voice_match'] = 0
        return res
