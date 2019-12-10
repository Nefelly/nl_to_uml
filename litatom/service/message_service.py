# coding: utf-8
import time
import datetime
from ..model import (
    UserMessage,
)
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from ..redis import RedisClient

from ..const import (
    DEFAULT_QUERY_LIMIT,
    MAX_TIME,
    NOT_AUTHORIZED,
    ONLINE_LIVE
)
from ..key import (
    REDIS_USER_NOT_MESSAGE_CACHE,
    REDIS_VISIT_RATE
)
from ..const import (
    ONE_HOUR
)
from ..util import get_time_info
from ..service import (
    UserService,
    FirebaseService,
    GlobalizationService
)
from flask import (
    request
)
redis_client = RedisClient()['lit']

class UserMessageService(object):
    PUSH_INTERVAL = 5 * ONE_HOUR
    MSG_LIKE = 'like'
    MSG_FOLLOW = 'follow'
    MSG_REPLY = 'reply'
    MSG_COMMENT = 'comment'
    MSG_VISIT_HOME = 'visit'
    
    MSG_MESSAGE_M = {
        MSG_LIKE: 'like your post',
        MSG_FOLLOW: 'start follow you',
        MSG_COMMENT: 'reply on your comment',
        MSG_REPLY: 'reply on your post'
    }

    MSG_MESSAGE_M_THAI = {
        MSG_LIKE: 'ถูกใจโพสต์ของคุณ',
        MSG_FOLLOW: 'เริ่มติดตามคุณ',
        MSG_COMMENT: 'ตอบกลับความเห็นของคุณ',
        MSG_REPLY: 'คอมเมนท์บนโพสต์ของคุณ'
    }

    @classmethod
    def get_message_m(cls):
        return cls.MSG_MESSAGE_M if not request.ip_thailand else cls.MSG_MESSAGE_M_THAI

    @classmethod
    def get_message(cls, m_type):
        tag_word = {
            cls.MSG_LIKE: 'like_feed',
            cls.MSG_FOLLOW: 'start_follow',
            cls.MSG_COMMENT: 'reply_comment',
            cls.MSG_REPLY: 'reply_feed',
            cls.MSG_VISIT_HOME: 'visit_home'
        }.get(m_type)
        return GlobalizationService.get_region_word(tag_word)

    @classmethod
    def msg_by_message_obj(cls, obj):
        if not obj:
            return {}
        return {
            'user_info': UserService.user_info_by_uid(obj.related_uid),
            'message':  cls.get_message(obj.m_type),
            'time_info': get_time_info(obj.create_time),
            'content': obj.content if obj.content else '',
            'message_id': str(obj.id),
            'feed_id': obj.related_feedid if obj.related_feedid else '',
            'message_type': obj.m_type
        }

    @classmethod
    def messages_by_uid(cls, user_id, start_ts=MAX_TIME, num=10):
        '''
        :return uid: online map
        :param uids:
        :return:
        '''
        res = []
        has_next = False
        next_start = -1
        no_msg_key = REDIS_USER_NOT_MESSAGE_CACHE.format(user_id=user_id)
        nomsg = redis_client.get(no_msg_key)
        if nomsg:
            return {
            'messages': res,
            'has_next': has_next,
            'next_start': next_start
            }, True
        objs = UserMessage.objects(uid=user_id, create_time__lte=start_ts).order_by('-create_time').limit(num + 1)
        objs = list(objs)
        #objs.reverse()   # 时间顺序错误

        if len(objs) == num + 1:
            has_next = True
            next_start = objs[-1].create_time
            objs = objs[:-1]
        for obj in objs:
            res.append(cls.msg_by_message_obj(obj))
        #UserMessage.objects(uid=user_id).limit(DEFAULT_QUERY_LIMIT).delete()
        if not objs:
            redis_client.set(no_msg_key, 1, ONLINE_LIVE)
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
    
    @classmethod
    def add_message(cls, user_id, related_user_id, m_type, related_feed_id=None, content=None):
        obj_id = UserMessage.add_message(user_id, related_user_id, m_type, related_feed_id, content)
        no_msg_key = REDIS_USER_NOT_MESSAGE_CACHE.format(user_id=user_id)
        redis_client.delete(no_msg_key)
        related_nickname = UserService.nickname_by_uid(related_user_id)
        # message = cls.get_message_m().get(m_type, '')
        message = cls.get_message(m_type)
        if content:
            message += ': "%s"' % content
        FirebaseService.send_to_user(user_id, related_nickname, message)
        return obj_id

    @classmethod
    def visit_message(cls, user_id, related_user_id):
        if not related_user_id or user_id == related_user_id:
            return False
        if not cls.should_push(user_id):
            return False
        cls.add_message(user_id, related_user_id, cls.MSG_VISIT_HOME)

    @classmethod
    def should_push(cls, user_id):
        if not cls._should_push_hour():
            return False
        key = REDIS_VISIT_RATE.format(user_id=user_id)
        if redis_client.get(key):
            return False
        online_time = UserService.uid_online_time(user_id)
        if int(time.time()) - online_time < ONE_HOUR:
            return False
        redis_client.set(key, 1, cls.PUSH_INTERVAL)

    @classmethod
    def _should_push_hour(cls):
        hour_now = datetime.datetime.now().hour
        return hour_now > 9
