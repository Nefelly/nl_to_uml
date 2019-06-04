# coding: utf-8
import time
import random
from ..redis import RedisClient

from ..model import (
    OnlineLimit,
    UserSetting,
    User
)
redis_client = RedisClient()['lit']

class UserFilterService(object):

    @classmethod
    def online_filter(cls, user_id, age_low, age_high, gender):
        print "*" * 100, user_id, age_low, age_high, gender
        obj = OnlineLimit.make(age_low, age_high, gender)
        user_setting = UserSetting.get_by_user_id(user_id)
        if user_setting:
            user_setting.online_limit = obj
            user_setting.save()
            return None, True
        else:
            user_setting = UserSetting()
            user_setting.user_id = user_id
            user_setting.online_limit = obj
            user_setting.save()
            return None, True

    @classmethod
    def get_filter_by_user_id(cls, user_id):
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting or not user_setting.online_limit:
            return {},  True
        return user_setting.online_limit.to_json(), True

    @classmethod
    def filter_by_age_gender(cls, user_id, target_uid):
        target_gender = None
        target_age = User.age_by_user_id(target_uid)
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting:
            return True
        limits = user_setting.online_limit
        if not limits:
            return True
        if limits.gender and target_gender and target_gender != limits.gender:
            return False
        if limits.age_low and target_age < limits.age_low:
            return False
        if limits.age_high and target_age > limits.age_high:
            return False
        return True