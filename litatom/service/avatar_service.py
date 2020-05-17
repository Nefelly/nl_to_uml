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
        return paid_avatars.get(fileid, {}).get('price', 0)

    @classmethod
    def can_change(cls, user_id, fileid):
        paid_avartars = Avatar.get_paid_avatars()
        if fileid in paid_avartars:
            if fileid not in UserAsset.get_avatars(user_id):
                return u'You have to buy first'
        return None

    @classmethod
    def get_avatars(cls, user_id=None):
        avatars = Avatar.get_avatars()
        if not user_id:
            return avatars
        asset_avatars = UserAsset.get_avatars(user_id)
        if not asset_avatars:
            return avatars
        for k in Avatar.paid_keys():
            for fielid in avatars[k]:
                if fielid in asset_avatars:
                    avatars[k][fielid]['buyed'] = True
                else:
                    avatars[k][fielid]['buyed'] = False
        return avatars
