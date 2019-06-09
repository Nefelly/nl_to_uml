# coding: utf-8
import time
import datetime
from ..model import (
    UserAction
)

class TrackActionService(object):

    @classmethod
    def create_action(cls, user_id, action, other_user_id=None, amount=None, remark=None):
        userAction = UserAction()
        userAction.user_id = user_id
        userAction.action = action
        if remark:
            userAction.remark = remark
        if other_user_id:
            userAction.other_user_id = other_user_id
        if amount:
            userAction.amount = amount
        userAction.create_time = int(time.time())
        userAction.create_date = datetime.datetime.now()
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
