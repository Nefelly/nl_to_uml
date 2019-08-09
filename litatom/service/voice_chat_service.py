# coding: utf-8
import time
import json
import StringIO
import gzip
import requests

from ..redis import RedisClient

from ..key import (
    REDIS_VOICE_CHAT_CALLED,
    REDIS_VOICE_CHAT_WAIT,
    REDIS_VOICE_CHAT_IN_CHAT
)
from ..model import (
    Blocked,
    Follow
)
from ..const import (
    ONE_MIN,
    ONE_DAY
)

redis_client = RedisClient()['lit']

class VoiceChatService(object):

    @classmethod
    def finish_chat(cls, user_id):
        self_key = REDIS_VOICE_CHAT_IN_CHAT.format(user_id=user_id)
        other_user_id = redis_client.get(self_key)
        if other_user_id:
            redis_client.delete(REDIS_VOICE_CHAT_IN_CHAT.format(user_id=other_user_id))
        redis_client.delete(self_key)
        return None, True

    @classmethod
    def invite(cls, user_id, target_user_id):
        self_in_chat_key = REDIS_VOICE_CHAT_IN_CHAT.format(user_id=user_id)
        self_wait = REDIS_VOICE_CHAT_WAIT.format(user_id=user_id)
        self_called = REDIS_VOICE_CHAT_WAIT.format(user_id=user_id)
        other_in_chat = redis_client.get(self_in_chat_key)
        if other_in_chat and other_in_chat != target_user_id:
            return u'you are in chat', False

        other_in_wait = redis_client.get(self_wait)
        if other_in_chat and other_in_wait != target_user_id:
            return u'you are calling others', False

        other_call = redis_client.get(self_called)
        if other_call and other_call != target_user_id:
            return u'you are being called', False

        if Blocked.in_block(target_user_id, user_id):
            return u'you have been blocked', False
        if not (Follow.in_follow(target_user_id, user_id) and Follow.in_follow(user_id, target_user_id)):
            return u'you should follow each other to launch a voice chat', False

        if redis_client.get(REDIS_VOICE_CHAT_IN_CHAT.format(user_id=target_user_id)):
            return u'He/She is in called', False

        target_called = redis_client.get(REDIS_VOICE_CHAT_CALLED.format(user_id=target_user_id))
        if target_called and target_called != user_id:
            return u'He/She is being called', False
        if redis_client.get(REDIS_VOICE_CHAT_WAIT.format(user_id=target_user_id)):
            return u'He/She is calling others', False
        redis_client.setex(self_wait, ONE_MIN, target_user_id)
        redis_client.setex(REDIS_VOICE_CHAT_CALLED.format(user_id=target_user_id), ONE_MIN + 3, user_id)
        return None, True

    @classmethod
    def accept(cls, user_id, target_user_id):
        self_called = REDIS_VOICE_CHAT_CALLED.format(user_id=user_id)
        calling = redis_client.get(self_called)
        if not calling or calling != target_user_id:
            return u'you are not called', False
        redis_client.setex(REDIS_VOICE_CHAT_IN_CHAT.format(user_id), ONE_DAY, target_user_id)
        redis_client.setex(REDIS_VOICE_CHAT_IN_CHAT.format(target_user_id), ONE_DAY, user_id)
        redis_client.delete(self_called)
        redis_client.delete(REDIS_VOICE_CHAT_WAIT.format(user_id=target_user_id))
        return None, True

    @classmethod
    def reject(cls, user_id, target_user_id):
        redis_client.delete(REDIS_VOICE_CHAT_IN_CHAT.format(user_id=target_user_id))
        return None, True

    @classmethod
    def cancel(cls, user_id):
        self_wait = REDIS_VOICE_CHAT_WAIT(user_id=user_id)
        other_user_id = redis_client.get(self_wait)
        redis_client.delete(self_wait)
        if other_user_id:
            redis_client.delete(REDIS_VOICE_CHAT_CALLED.format(user_id=other_user_id))
        return None, True
