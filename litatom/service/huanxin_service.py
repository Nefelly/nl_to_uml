# coding: utf-8
import base64
import hashlib
import json
import traceback
import logging
import requests
import time
import datetime
import random
from hendrix.conf import setting
sys_rng = random.SystemRandom()
from ..redis import RedisClient
from ..model import (
    RedisLock
)
from ..key import (
    REDIS_HUANXIN_ACCESS_TOKEN,
    REDIS_HUANXIN_ACCESS_TOKEN_EXPIRE
)
from ..util import (
    passwdhash
)

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class HuanxinService(object):
    HUANXIN_SETTING = setting.HUANXIN_ACCOUNT
    ORG_NAME = HUANXIN_SETTING.get('org_name', '1102190223222824')
    APP_NAME = HUANXIN_SETTING.get('app_name', 'lit')
    APP_KEY = '%s#%s' % (ORG_NAME, APP_NAME)
    HOST = 'https://a1.easemob.com'
    APP_URL = '%(HOST)s/%(ORG_NAME)s/%(APP_NAME)s/' % dict(HOST=HOST, ORG_NAME=ORG_NAME, APP_NAME=APP_NAME)

    CLIENT_ID = HUANXIN_SETTING.get('client_id', 'YXA6ALfHYDd7EemQqCO501ONvQ')
    CLIENT_SECRET = HUANXIN_SETTING.get('client_secret', 'YXA6AH1kFGkcUc67KcpClt5rWA23zv4')
    '''
    docs :http://docs-im.easemob.com/start/100serverintegration/20users
    download chat record:http://docs-im.easemob.com/im/server/basics/chatrecord
    '''

    @classmethod
    def gen_id_pwd(cls):
        raw_id = None
        pwd = None
        for i in range(3):
            td = datetime.datetime.now() - datetime.datetime(1980, 1, 1)
            ss = (td.seconds + td.days * 24 * 3600)
            rs = sys_rng.randint(10 ** 4, 10 ** 4 * 9)
            raw_id = 'love%d%d' % (ss, rs)
            pwd = passwdhash(raw_id)
            status = cls.create_user(raw_id, pwd)
            if status:
                break
        return raw_id, pwd

    @classmethod
    def get_access_token(cls):
        lock_name = 'redis_mutex'
        time_now = int(time.time())
        str_expire = redis_client.get(REDIS_HUANXIN_ACCESS_TOKEN_EXPIRE)
        expire = int(str_expire) if str_expire else 0
        if expire - 10 > time_now:   # - 10 for subtle time diffrence
            access_token = redis_client.get(REDIS_HUANXIN_ACCESS_TOKEN)
            if access_token:
                return access_token

        url = cls.APP_URL + 'token'

        try:
            data = {
                'grant_type': 'client_credentials',
                'client_id': cls.CLIENT_ID,
                'client_secret': cls.CLIENT_SECRET
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
        url = cls.APP_URL + 'users/%s/offline_msg_count' % user_name

        access_token = cls.get_access_token()
        if not access_token:
            return {}
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.get(url, verify=False, headers=headers).json()
            return response.get('data')
        except Exception, e:
            traceback.print_exc()
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return {}

    @classmethod
    def offline_msg_desc(cls, user_name, msg_id):
        url = cls.APP_URL + 'users/%s/offline_msg_status/%s' % (user_name, msg_id)

        access_token = cls.get_access_token()
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
            traceback.print_exc()
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', user_name, e)
            return {}

    @classmethod
    def log_out(cls, user_name):
        url = cls.APP_URL + 'users/%s/disconnect' % user_name

        access_token = cls.get_access_token()
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
            traceback.print_exc()
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', user_name, e)
            return {}

    @classmethod
    def block_user(cls, source_user_name, dest_user_name):
        url = cls.APP_URL + 'users/%s/blocks/users' % source_user_name

        access_token = cls.get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.post(url, verify=False, headers=headers, data=json.dumps({'usernames': [dest_user_name]})).json()
            assert response.get('data')[0]
            return True
        except Exception, e:
            traceback.print_exc()
            logger.error('Error block huanxin, user_id: %r, err: %r', source_user_name, e)
            return {}

    @classmethod
    def unblock_user(cls, source_user_name, dest_user_name):
        url = cls.APP_URL + 'users/%s/blocks/users/%s' % (source_user_name, dest_user_name)

        access_token = cls.get_access_token()
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
            traceback.print_exc()
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return {}

    @classmethod
    def add_friend(cls, source_user_name, dest_user_name):
        url = cls.APP_URL + 'users/%s/contacts/users/%s' % (source_user_name, dest_user_name)

        access_token = cls.get_access_token()
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
            traceback.print_exc()
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return False

    @classmethod
    def del_friend(cls, source_user_name, dest_user_name):
        url = cls.APP_URL + 'users/%s/contacts/users/%s' % (source_user_name, dest_user_name)

        access_token = cls.get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.delete(url, verify=False, headers=headers, data={}).json()
            assert response.get('entities')[0]['username']
            return True
        except Exception, e:
            traceback.print_exc()
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return False


    @classmethod
    def update_nickname(cls, user_name, nickname):
        url = cls.APP_URL + 'users/%s' % user_name

        access_token = cls.get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.put(url, verify=False, headers=headers, data=json.dumps({'nickname': nickname})).json()
            assert response.get('entities')[0]['nickname']
            return True
        except Exception, e:
            traceback.print_exc()
            logger.error('Error create huanxin update_nickname user, user_id: %r, err: %r', user_name, e)
            return {}

    @classmethod
    def get_user(cls, user_name):
        url = cls.APP_URL + 'users/%s' % user_name

        access_token = cls.get_access_token()
        if not access_token:
            return {}
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.get(url, verify=False, headers=headers).json()
            return response.get('entities')[0]
        except Exception, e:
            traceback.print_exc()
            logger.error('Error create huanxin get user, user_id: %r, err: %r', user_name, e)
            return {}


    @classmethod
    def create_user(cls, user_name, password):
        url = cls.APP_URL + 'users'

        access_token = cls.get_access_token()
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
            traceback.print_exc()
            logger.error('Error create huanxin user, user_name: %r, err: %r', user_name, e)
            return False

    @classmethod
    def delete_user(cls, user_name):
        url = '%(HOST)s/%(ORG_NAME)s/%(APP_NAME)s/users/%(user_name)s'
        url = url % dict(HOST=cls.HOST, ORG_NAME=cls.ORG_NAME, APP_NAME=cls.APP_NAME, user_name=user_name)

        access_token = cls.get_access_token()
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
            traceback.print_exc()
            logger.error('Error create huanxin get user, user_id: %r, err: %r', user_name, e)
            return False

    @classmethod
    def active_user(cls, user_name):
        url = cls.APP_URL + 'users/%s/activate' % user_name

        access_token = cls.get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.post(url, verify=False, headers=headers, data=json.dumps({})).json()
            assert response.get('action')
            return True
        except Exception, e:
            traceback.print_exc()
            logger.error('Error active huanxin, user_id: %r, err: %r', user_name, e)
            return {}

    @classmethod
    def deactive_user(cls, user_name):
        url = cls.APP_URL + 'users/%s/deactivate' % user_name

        access_token = cls.get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.post(url, verify=False, headers=headers).json()
            assert response.get('entities')[0]['username']
            return True
        except Exception, e:
            traceback.print_exc()
            logger.error('Error deactive huanxin  add friend, user_id: %r, err: %r', user_name, e)
            return {}
    