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


class HuanxinMessage(Document):
    meta = {
        'strict': False,
        'db_alias': 'huanxin_message'
    }
    '''
    http://docs-im.easemob.com/im/server/basics/chatrecord
    {
        "msg_id": "5I02W-16-8278a",
        "timestamp": 1403099033211,
        "direction":"outgoing",
        "to": "1402541206787",
        "from": "zw123",
        "chat_type": "chat",
        "payload": {
            "bodies": [
              {
                 //下面会将不同的消息类型进行说明
              }
            ],
            "ext": {
                "key1": "value1",
                   ...
             },
             "from":"zw123",
             "to":"1402541206787"
        }
    }
    '''
    msg_id = StringField(required=True, unique=True)
    user_id = StringField(required=True)
    to_user_id = StringField(required=True)
    huanxin_id = StringField()
    to_huanxin_id  = StringField()
    payload = StringField()
    msg = StringField()
    msg_type = StringField()
    create_time = IntField(required=True)

    @classmethod
    def create(cls, data, user_id, to_user_id):
        obj = cls()
        obj.msg_id = data.get('msg_id')
        obj.user_id = user_id
        obj.to_user_id = to_user_id
        obj.huanxin_id = data['from']
        obj.to_huanxin_id = data['to']
        payload = data['payload']
        obj.payload = json.dumps(payload)
        body = payload['bodies'][0]
        msg_type = body['type']
        if msg_type == 'txt':
            msg = body['msg']
        else:
            msg = body['url']
        obj.msg = msg
        obj.msg_type = msg_type
        obj.create_time = data['timestamp']
        obj.save()
        return True

    @classmethod
    def get_by_user_ids(cls, from_user_id, to_user_id=None):
        return {}

