# coding: utf-8
from ..redis import RedisClient
from ..model import (
    OnlineLimit,
    UserSetting,
    User
)
from ..service import (
    GlobalizationService
)
from ..const import (
    ALL_FILTER
)

redis_client = RedisClient()['lit']

class UserFilterService(object):
    HIGHEST_AGE = 25

    @classmethod
    def online_filter(cls, user_id, age_low, age_high, gender, is_new=False):
        obj = OnlineLimit.make(age_low, age_high, gender, is_new)
        user_setting = UserSetting.get_by_user_id(user_id)
        if ALL_FILTER:
            msg = {"message": GlobalizationService.get_region_word('filter_inform')}
        else:
            msg = None
        if user_setting:
            user_setting.online_limit = obj
            user_setting.save()
            return msg, True
        else:
            user_setting = UserSetting()
            user_setting.user_id = user_id
            user_setting.online_limit = obj
            user_setting.save()
            return msg, True

    @classmethod
    def is_gender_filtered(cls, user_id):
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting:
            return False
        limits = user_setting.online_limit
        if not limits:
            return False
        if limits.gender:
            return True

    @classmethod
    def get_filter_by_user_id(cls, user_id):
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting or not user_setting.online_limit:
            return {},  True
        return user_setting.online_limit.to_json(), True

    @classmethod
    def is_homo(cls, user_id, gender):
        if not ALL_FILTER:
            return False
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting or not user_setting.online_limit or user_setting.online_limit.gender != gender:
            return False
        return True

    @classmethod
    def batch_filter_by_age(cls, user_id, target_uids, need_new=False):
        res = []
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting or not user_setting.online_limit:
            return target_uids
        limits = user_setting.online_limit
        if need_new and not limits.is_new:
            return target_uids
        uid_ages_m = User.batch_age_by_user_ids(target_uids)
        for uid in target_uids:
            age = uid_ages_m.get(uid, User.DEFUALT_AGE)
            if limits.age_low and age < limits.age_low:
                continue
            if limits.age_high and limits.age_high != cls.HIGHEST_AGE and age > limits.age_high:
                continue
            res.append(uid)
        return res

    @classmethod
    def batch_filter_two_way(cls, user_id, target_uids, need_new=False):
        ''' need_new  需要是新的过滤 过滤才生效， 故而非新过滤 则直接返回'''
        target_uids = cls.batch_filter_by_age(user_id, target_uids, need_new)
        if not target_uids:
            return target_uids
        user_age = User.age_by_user_id(user_id)
        user_settings_m = UserSetting.batch_get_by_user_ids(target_uids)
        res = []
        for uid in target_uids:
            user_setting = user_settings_m.get(uid, None)
            if not user_setting or not user_setting.online_limit or (need_new and not user_setting.online_limit.is_new):
                res.append(uid)
                continue
            limits = user_setting.online_limit
            if limits.age_low and user_age < limits.age_low:
                continue
            if limits.age_high and limits.age_high != cls.HIGHEST_AGE and user_age > limits.age_high:
                continue
            res.append(uid)
        return res

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
        if limits.age_high and limits.age_high != cls.HIGHEST_AGE and target_age > limits.age_high:
            return False
        return True
