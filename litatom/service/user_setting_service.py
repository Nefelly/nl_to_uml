# coding: utf-8
import time
import json
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
    TYPE_VOICE_TENCENT
)
from ..key import (
    REDIS_SETTINGS_KEYS
)

from ..service import GlobalizationService
redis_client = RedisClient()['lit']

class UserSettingService(object):

    @classmethod
    def change_setting(cls, data):
        redis_client.set(REDIS_SETTINGS_KEYS, json.dumps(data))
        return None, True

    @classmethod
    def get_settings(cls, user_id=None):
        if not user_id and request.uuid:
            Uuids.create(request.uuid)
        res = {
            'need_login': True,
            'max_voice_time': ONE_HOUR,
            'pop_good_rate': True,
            'prior_voice': TYPE_VOICE_TENCENT,   # agora 声网，
            'phone_login_without_code': True,
            'ad_rule': {
                'interval': 5,
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
            }
        }
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
        modules_open = {
            "soul_match": 1,
            "video_match": 1,
            "voice_match": 1
        }

        res['modules_open'] = modules_open
        if setting.IS_DEV:
            should_change = False
            cached_setting_str = redis_client.get(REDIS_SETTINGS_KEYS)
            if not cached_setting_str:
                should_change = True
            else:
                cached_setting = json.loads(cached_setting_str)
                if len(cached_setting.keys()) < len(res.keys()):
                    should_change = True

                    print should_change, '555555a'
                else:
                    for key in cached_setting:
                        if isinstance(cached_setting[key], dict):
                            if len(cached_setting[key].keys()) < len(res[key].keys()):
                                should_change = True

                                print should_change, '555444'
                                break
            if should_change:
                print should_change, '555555'
                redis_client.delete(REDIS_SETTINGS_KEYS)
                redis_client.set(REDIS_SETTINGS_KEYS, json.dumps(res))
            else:
                res = cached_setting
        if region not in [GlobalizationService.REGION_TH]:
            # if request.version != '2.5.3':
               res['modules_open']['video_match'] = 0
        return res
