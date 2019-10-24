# coding: utf-8
import time
from  flask import (
    request
)
from ..const import (
    ONE_DAY
)
from ..util import date_to_int_time
from ..model import (
    User,
    UserSetting
)
from ..const import (
    ONE_HOUR
)
from ..service import GlobalizationService


class UserSettingService(object):

    @classmethod
    def get_settings(cls, user_id=None):
        res = {
            'need_login': True,
            'max_voice_time': ONE_HOUR,
            'pop_good_rate': True,
            'ad_rule': {
                'interval': 5
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
        if region != GlobalizationService.REGION_TH:
            # if request.version != '2.5.3':
                modules_open['video_match'] = 0
        res['modules_open'] = modules_open
        return res
