# coding: utf-8
import json
import time
import traceback
from ..model import (
    Avatar,
    UserAsset
)
import logging
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class AvatarService(object):
    '''
    '''

    @classmethod
    def get_avatar_price(cls, fileid):
        paid_avatars = Avatar.get_paid_avatars()
        return paid_avatars.get(fileid, 0)

    @classmethod
    def can_change(cls, user_id, fileid):
        paid_avartars = Avatar.get_paid_avatars()
        if fileid in paid_avartars:
            if fileid not in UserAsset.get_avatars(user_id):
                return u'You have to buy first', False
        return None, True
