# coding: utf-8
import time
import StringIO
import gzip
import requests

from ..redis import RedisClient

from ..key import (
    REDIS_HUANXIN_USER
)
import sys
from flask import request
from ..service import (
    UserService,
    HuanxinService
)
from ..model import (
    HuanxinMessage
)
redis_client = RedisClient()['lit']

class ChatRecordService(object):

    @classmethod
    def records_by_hour(cls, hour):
        url = HuanxinService.chat_msgs_by_hour(hour)
        if not url:
            return []
        compressedstream = StringIO.StringIO(requests.get(url).content)
        gz = gzip.GzipFile(fileobj=compressedstream)
        data = gz.read()
        lines = data.split('\n')
        res = [json.loads(line) for line in lines]
        return res

    @classmethod
    def uid_by_huanxinid(cls, huanxin_id):
        key = REDIS_HUANXIN_USER.format(huanxin_id=huanxin_id)
        res = redis_client.get(key)
        if res:
            return res
        uid = UserService.uid_by_huanxin_id(huanxin_id)
        if uid:
            redis_client.set(key, uid, 300)
        return uid


    @classmethod
    def save_to_db(cls, data):
        user_id = cls.uid_by_huanxinid(data['from'])
        to_user_id = cls.uid_by_huanxinid(data['to'])
        HuanxinMessage.create(data, user_id, to_user_id)
        return True