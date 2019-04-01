# coding: utf-8
import time
import requests
import logging
import traceback
from ..redis import RedisClient
from ..model import FirebaseInfo

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class FirebaseService(object):
    '''
    docs:
    https://blog.csdn.net/java20131115/article/details/52869423
    https://blog.csdn.net/juemuren444/article/details/63833401

    account_info:https://console.firebase.google.com/project/litatom/settings/cloudmessaging/android:com.litatom.app
    '''

    SERVER_KEY = 'AAAAt1lsa8A:APA91bFovgbJfA6t6Hf47TxSIu_Oqk4kJcQL69Ew-Y2A23qLW8ZafWpM_CQr3H_1EiTWS4zYVaVLxLrxMb3zZnuUx6asLanr2OCIcgBGHRbnhxLTIYHIjn0rXtZfeu22O6twhcrGUNxR'
    MY_ID = '787479292864'
    SEND_URL = 'https://fcm.googleapis.com/fcm/send'

    @classmethod
    def add_token(cls, user_id, token):
        obj = FirebaseInfo.get_by_user_id(user_id)
        if not token:
            return  u'lake of field token', False
        if not obj:
            obj = FirebaseInfo()
        obj.user_id = user_id
        obj.user_token = token
        obj.create_time = int(time.time())
        obj.save()
        return None, True

    @classmethod
    def send_to_user(cls, user_id, title, text):
        obj = FirebaseInfo.get_by_user_id(user_id)
        if not obj:
            return u'no firebase token', False
        data = {
            'notification': {
                'title': title,
                'text': text
            },
            'to': obj.user_token
        }

        headers = {
            'Content-Type':'application/json; charset=utf-8',
            'Authorization': 'key=%s' % cls.SERVER_KEY
        }
        try:
            response = requests.post(cls.SEND_URL, verify=False, headers=headers, json=data).json()
            print response
            assert response.get('data')[0]
            return True
        except Exception, e:
            traceback.print_exc()
            logger.error('firebase send  error, user_id: %r, err: %r', user_id, e)
            return False