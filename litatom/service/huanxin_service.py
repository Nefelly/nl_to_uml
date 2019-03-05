# coding: utf-8
import base64
import hashlib
import json
import logging
import requests
import time
from ..redis import RedisClient
from ..model import (
    RedisLock
)
from ..key import (
    REDIS_HUANXIN_ACCESS_TOKEN,
    REDIS_HUANXIN_ACCESS_TOKEN_EXPIRE
)

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class HuanxinService(object):
    ORG_NAME = '1102190223222824'
    APP_NAME = 'lit'
    APP_KEY = '%s#%s' % (ORG_NAME, APP_NAME)
    HOST = 'https://a1.easemob.com/'
    APP_URL = '%(HOST)/%(ORG_NAME)/%(APP_NAME)/' % dict(HOST=HOST, ORG_NAME=ORG_NAME, APP_NAME=APP_NAME)

    CLIENT_ID = 'YXA6ALfHYDd7EemQqCO501ONvQ'
    CLIENT_SECRET = 'YXA6AH1kFGkcUc67KcpClt5rWA23zv4'
    '''
    docs :http://docs-im.easemob.com/start/100serverintegration/20users
    '''

    @classmethod
    def get_access_token(cls):
        lock_name = 'redis_mutex'
        time_now = time.time()
        expire = int(redis_client.get(REDIS_HUANXIN_ACCESS_TOKEN_EXPIRE))
        if expire - 10 > time_now:   # - 10 for subtle time diffrence
            access_token = redis_client.get(REDIS_HUANXIN_ACCESS_TOKEN)
            if access_token:
                return access_token

        url = APP_URL + 'token'

        try:
            data = {
                'grant_type': 'client_credentials',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            }
            lock = RedisLock.get_mutex(lock_name)
            if not lock:
                time.sleep(1)
                return redis_client.get(REDIS_HUANXIN_ACCESS_TOKEN)
            response = requests.post(url, verify=False, json=data).json()
            access_token = response.get('access_token')
            expires_in = int(response.get('expires_in'))
            redis_client.set(REDIS_HUANXIN_ACCESS_TOKEN_EXPIRE, time_now + expires_in)
            redis_client.set(REDIS_HUANXIN_ACCESS_TOKEN, access_token)
            RedisLock.release_mutex(lock_name)
            return access_token
        except Exception, e:
            logger.error('Error getting huanxin access_token, err: %r', e)
            return

    @classmethod
    def offline_msg_cnt(cls, user_name):
        url = APP_URL + 'users/%s/offline_msg_count' % user_name

        access_token = get_access_token()
        if not access_token:
            return {}
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.get(url, verify=False, headers=headers).json()
            return response.get('data')
        except Exception, e:
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return {}

    @classmethod
    def offline_msg_desc(cls, user_name, msg_id):
        url = APP_URL + 'users/%s/offline_msg_status' % (user_name, msg_id)

        access_token = get_access_token()
        if not access_token:
            return {}
        headers = {
            'Content-Type':'application/json',
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.get(url, verify=False, headers=headers).json()
            return response.get('data')
        except Exception, e:
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return {}

    @classmethod
    def log_out(cls, user_name):
        url = APP_URL + 'users/%s/disconnect' % user_name

        access_token = get_access_token()
        if not access_token:
            return False
        headers = {
            'Content-Type':'application/json',
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.get(url, verify=False, headers=headers).json()
            return response.get('data')['result']
        except Exception, e:
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', user_name, e)
            return {}

    @classmethod
    def block_user(cls, source_user_name, dest_user_name):
        url = APP_URL + 'users/%s/blocks/users' % source_user_name

        access_token = get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.post(url, verify=False, headers=headers, data={'usernames': [dest_user_name]}).json()
            assert response.get('entities')[0]['username']
            return True
        except Exception, e:
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', user_name, e)
            return {}

    @classmethod
    def unblock_user(cls, source_user_name, dest_user_name):
        url = APP_URL + 'users/%s/blocks/users/%s' % (source_user_name, dest_user_name)

        access_token = get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.delete(url, verify=False, headers=headers).json()
            assert response.get('entities')[0]['username']
            return True
        except Exception, e:
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return {}

    @classmethod
    def add_friend(cls, source_user_name, dest_user_name):
        url = APP_URL + 'users/%s/contacts/users/%s' % (source_user_name, dest_user_name)

        access_token = get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.post(url, verify=False, headers=headers, data={}).json()
            assert response.get('entities')[0]['username']
            return True
        except Exception, e:
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return False

    @classmethod
    def update_nickname(cls, user_name, nickname):
        url = APP_URL + 'users/%s' % user_name

        access_token = get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.put(url, verify=False, headers=headers, data={'nickname': nickname}).json()
            assert response.get('entities')[0]['nickname']
            return True
        except Exception, e:
            logger.error('Error create huanxin update_nickname user, user_id: %r, err: %r', user_name, e)
            return {}

    @classmethod
    def get_user(cls, user_name):
        url = APP_URL + user_name

        access_token = get_access_token()
        if not access_token:
            return {}
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.get(url, verify=False, headers=headers).json()
            return response.get('entities')[0]
        except Exception, e:
            logger.error('Error create huanxin get user, user_id: %r, err: %r', user_name, e)
            return {}


    @classmethod
    def create_user(cls, user_name, password):
        url = APP_URL + 'users'

        access_token = get_access_token()
        if not access_token:
            return False
        headers = {
            'Content-Type':'application/json',
            'Authorization':'Bearer %s' % access_token
        }
        data = {'username': user_name, 'password': password}
        try:
            response = requests.post(url, verify=False, headers=headers, json=data).json()
            assert response.get('entities')[0]['username']
            return True
        except Exception, e:
            logger.error('Error create huanxin user, user_name: %r, err: %r', user_name, e)
            return False

    @classmethod
    def delete_user(cls, user_name):
        url = '%(HOST)/%(ORG_NAME)/%(APP_NAME)/users/%(user_name)'
        url = url % dict(HOST=HOST, ORG_NAME=ORG_NAME, APP_NAME=APP_NAME, user_name=user_name)

        access_token = get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.delete(url, verify=False, headers=headers).json()
            assert response.get('entities')[0]['username']
            return True
        except Exception, e:
            logger.error('Error create huanxin get user, user_id: %r, err: %r', user_name, e)
            return False