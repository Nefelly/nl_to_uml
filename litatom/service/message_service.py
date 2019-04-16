# coding: utf-8
import time
from ..model import (
    UserMessage,
)
from ..const import (
    DEFAULT_QUERY_LIMIT,
    MAX_TIME,
    NOT_AUTHORIZED
)
from ..util import get_time_info
from ..service import (
    UserService
)
from flask import (
    request
)
class UserMessageService(object):
    MSG_MESSAGE_M = {
        UserMessage.MSG_LIKE: 'like your feed',
        UserMessage.MSG_FOLLOW: 'start follow you',
        UserMessage.MSG_COMMENT: 'reply on your comment',
        UserMessage.MSG_REPLY: 'reply on your feed'
    }

    MSG_MESSAGE_M_THAI = {
        UserMessage.MSG_LIKE: 'กใจโพสต์ของคุณ',
        UserMessage.MSG_FOLLOW: 'เริ่มติดตามคุณ',
        UserMessage.MSG_COMMENT: 'reply on your comment',
        UserMessage.MSG_REPLY: 'คอมเมนท์บนโพสต์ของคุณ'
    }

    @classmethod
    def msg_by_message_obj(cls, obj):
        if not obj:
            return {}
        message_m = cls.MSG_MESSAGE_M if not request.ip_thailand else cls.MSG_MESSAGE_M_THAI
        return {
            'user_info': UserService.user_info_by_uid(obj.related_uid),
            'message':  message_m.get(obj.m_type, ''),
            'time_info': get_time_info(obj.create_time),
            'content': obj.content if obj.content else '',
            'message_id': str(obj.id),
            'feed_id': obj.related_feedid if obj.related_feedid else '',
        }

    @classmethod
    def messages_by_uid(cls, user_id, start_ts=MAX_TIME, num=10):
        '''
        :return uid: online map
        :param uids:
        :return:
        '''
        res = []
        objs = UserMessage.objects(uid=user_id, create_time__lte=start_ts).limit(num + 1)
        objs = list(objs)
        objs.reverse()   # 时间顺序错误
        has_next = False
        next_start = -1
        if len(objs) == num + 1:
            has_next = True
            next_start = objs[-1].create_time
            objs = objs[:-1]
        for obj in objs:
            res.append(cls.msg_by_message_obj(obj))
        #UserMessage.objects(uid=user_id).limit(DEFAULT_QUERY_LIMIT).delete()
        ret = {
            'messages': res,
            'has_next': has_next,
            'next_start': next_start
        }
        return ret, True

    @classmethod
    def read_message(cls, user_id, message_id):
        obj = UserMessage.get_by_id(message_id)
        if not obj:
            return None, True
        if obj.uid != user_id:
            return NOT_AUTHORIZED, False
        obj.delete()
        return None, True
