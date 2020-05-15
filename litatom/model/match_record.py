# coding: utf-8
import datetime
import json
import bson
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)


class MatchRecord(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }


    user_id1 = StringField(required=True)
    user_id2 = StringField(required=True)
    match_type = StringField(required=True)
    quit_user = StringField()
    match_succ_time = IntField()
    inter_time = IntField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, user_id1, user_id2, match_type, quit_user, match_succ_time, inter_time):
        obj = cls()
        obj.user_id1 = user_id1
        obj.user_id2 = user_id2
        obj.match_type = match_type
        obj.quit_user = quit_user
        obj.match_succ_time = match_succ_time
        obj.inter_time = inter_time
        obj.save()
        return obj


class MatchHistory(Document):
    '''

    '''
    meta = {
        'strict': False,
        'db_alias': 'relations',
        'shard_key': {'user_id': 'hashed'}
    }
    STRANGER = 1
    SEND_REQUEST = 2
    WAIT_TO_ACCEPT = 3
    FRIENDS = 4

    user_id = StringField(required=True)
    # match_id = StringField()  # 为加双方user_id及时间戳hash而成的id
    # match_type = StringField(required=True)
    other_user_id = StringField(required=True)
    friend_status = IntField()
    match_success_time = IntField()
    chat_time = IntField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def add_match(cls, user_id, other_user_id, match_success_time, chat_time, is_friend):
        friend_status = cls.FRIENDS if is_friend else cls.STRANGER
        obj = cls(user_id=user_id, other_user_id=other_user_id, match_success_time=match_success_time, chat_time=chat_time,
                  friend_status=friend_status)
        obj.save()

    @classmethod
    def get_history(cls, user_id, page_num, num):
        return cls.objects(user_id=user_id).order_by('-match_success_time').skip(page_num * num).limit(num)


    @classmethod
    def get_specified(cls, user_id, other_user_id, match_success_time):
        return cls.objects(user_id=user_id, other_user_id=other_user_id, match_success_time=match_success_time).first()

    def to_json(self):
        return {
            'other_user_id': self.other_user_id,
            'match_success_time': self.match_success_time,
            'chat_time': self.chat_time,
            'friend_status': self.friend_status
        }

