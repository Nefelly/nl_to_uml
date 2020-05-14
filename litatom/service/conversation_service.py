# coding: utf-8
import json
import time
import traceback
import logging
from ..model import UserConversation
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class ConversationService(object):
    '''
    '''

    @classmethod
    def add_conversation(cls, user_id, other_user_id, conversation_id, from_type=None):
        UserConversation.add_conversation(user_id, other_user_id, conversation_id, from_type)
        return None, True

    @classmethod
    def del_conversation(cls, user_id, conversation_id):
        UserConversation.del_conversation(user_id, conversation_id)
        return None, True

    @classmethod
    def get_conversations(cls, user_id):
        conversations, pinned_conversation = UserConversation.get_by_user_id(user_id)
        data = {
            "conversations": conversations
        }
        if pinned_conversation:
            data['pinned'] = pinned_conversation
        return data, True
    
    @classmethod
    def pin_conversation(cls, user_id, other_user_id, conversation_id):
        UserConversation.pin_conversation(user_id, other_user_id, conversation_id)
        return None, True
    
    @classmethod
    def unpin_conversation(cls, user_id, other_user_id, conversation_id):
        UserConversation.unpin_conversation(user_id, conversation_id)
        return None, True
