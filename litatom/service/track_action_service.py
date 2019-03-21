# coding: utf-8
import time
from ..model import (
    UserAction
)

class TrackActionService(object):

    @classmethod
    def create_action(cls, user_id, action, remark=None):
        userAction = UserAction()
        userAction.user_id = user_id
        userAction.action = action
        if remark:
            userAction.remark = remark
        userAction.create_time = int(time.time())
        userAction.save()
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
