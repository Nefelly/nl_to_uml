# coding: utf-8
import time
from ..model import (
    UserAction
)

class TrackActionService(object):

    @classmethod
    def create_action(cls, user_id, action, remark=None):
        action = UserAction()
        action.user_id = user_id
        action.action = action
        if remark:
            action.remark = remark
        action.create_time = int(time.time())
        action.save()
        return True


    @classmethod
    def action_by_uid(cls, user_id):
        '''
        :return uid: online map
        :param uids:
        :return:
        '''
        res = map(UserAction.to_json, UserAction.get_by_user_id(user_id))
        return res, True
