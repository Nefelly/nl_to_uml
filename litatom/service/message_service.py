# coding: utf-8
import time
from ..model import (
    UserMessage,
)
from ..const import (
    DEFAULT_QUERY_LIMIT
)
from ..util import get_time_info
from ..service import (
    UserService
)
class UserMessageService(object):
    MSG_MESSAGE_M = {
        UserMessage.MSG_LIKE: 'like your feed',
        UserMessage.MSG_FOLLOW: 'start follow you',
        UserMessage.MSG_COMMENT: 'comment on your feed',
        UserMessage.MSG_REPLY: 'reply on your comment'
    }

    @classmethod
    def msg_by_message_obj(cls, obj):
        if not obj:
            return {}
        return {
            'user_info': UserService.user_info_by_uid(obj.uid),
            'message':  cls.MSG_MESSAGE_M.get(obj.m_type, ''),
            'time_info': get_time_info(obj.create_time),
            'content': obj.content if obj.content else ''
        }

    @classmethod
    def messages_by_uid_and_del(cls, user_id):
        '''
        :return uid: online map
        :param uids:
        :return:
        '''
        res = []
        next_start = -1
        feeds = Feed.objects(user_id=user_id, create_time__lte=start_ts).limit(num + 1)
        feeds = list(feeds)
        feeds.reverse()   # 时间顺序错误
        has_next = False
        if len(feeds) == num + 1:
            has_next = True
            next_start = feeds[-1].create_time
            feeds = feeds[:-1]
        return {
                   'feeds': map(cls._feed_info, feeds, [visitor_user_id for el in feeds]),
                   'has_next': has_next,
                   'next_start': next_start
               }, True

        objs = UserMessage.objects(uid=user_id).order_by('-create_time').limit(DEFAULT_QUERY_LIMIT)
        for obj in objs:
            res.append(cls.msg_by_message_obj(obj))
        #UserMessage.objects(uid=user_id).limit(DEFAULT_QUERY_LIMIT).delete()
        return res, True
