# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    UserModel,
    MatchRecord
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class UserModelService(object):
    '''
    '''

    @classmethod
    def cal_match(cls, match_record):
        if not match_record:
            return
        uid1 = match_record.user_id1
        uid2 = match_record.user_id2
        inter_time = match_record.inter_time
        cls.add_match_by_uid_inter(uid1, inter_time)
        cls.add_match_by_uid_inter(uid2, inter_time)

    @classmethod
    def add_match_by_uid_inter(cls, user_id, inter_time):
        return UserModel.add_match_record(user_id, inter_time)

    @classmethod
    def build_match(cls):
        mm = {}
        for _ in MatchRecord.objects():
            u1 = _.user_id1
            u2 = _.user_id2
            if not mm.get(u1):
                mm[u1] = [_.inter_time]
            else:
                mm[u1].append(_.inter_time)
            if not mm.get(u2):
                mm[u2] = [_.inter_time]
            else:
                mm[u2].append(_.inter_time)
        for _ in mm:
            UserModel.add_match_record(_, sum(mm[_]), len(mm[_]))