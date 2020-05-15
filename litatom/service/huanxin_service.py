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
    REDIS_HUANXIN_ACCESS_TOKEN_EXPIRE,
    REDIS_HUANXIN_SIG_ACCESS_TOKEN,
    REDIS_HUANXIN_SIG_ACCESS_TOKEN_EXPIRE,
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
    SIG_HOST = 'https://a1-sgp.easemob.com'   # 新加坡
    APP_URL = '%(HOST)s/%(ORG_NAME)s/%(APP_NAME)s/' % dict(HOST=HOST, ORG_NAME=ORG_NAME, APP_NAME=APP_NAME)
    SIG_APP_URL = '%(HOST)s/%(ORG_NAME)s/%(APP_NAME)s/' % dict(HOST=SIG_HOST, ORG_NAME=ORG_NAME, APP_NAME=APP_NAME)
    APP_URL = SIG_APP_URL
    TRY_TIMES = 3

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
    def get_access_token(cls, is_sig=False):
        token_expire_key, access_token_key = REDIS_HUANXIN_ACCESS_TOKEN_EXPIRE, REDIS_HUANXIN_ACCESS_TOKEN
        if is_sig:
            token_expire_key, access_token_key = REDIS_HUANXIN_SIG_ACCESS_TOKEN_EXPIRE, REDIS_HUANXIN_SIG_ACCESS_TOKEN
        lock_name = 'redis_mutex'
        time_now = int(time.time())
        str_expire = redis_client.get(token_expire_key)
        expire = int(str_expire) if str_expire else 0
        if expire - 10 > time_now:   # - 10 for subtle time diffrence
            access_token = redis_client.get(access_token_key)
            if access_token:
                return access_token

        url = cls.APP_URL + 'token'
        if is_sig:
            url = cls.SIG_APP_URL + 'token'
        try:
            data = {
                'grant_type': 'client_credentials',
                'client_id': cls.CLIENT_ID,
                'client_secret': cls.CLIENT_SECRET
            }
            lock = RedisLock.get_mutex(lock_name)
            if not lock:
                time.sleep(1)
                return redis_client.get(access_token_key)
            response = requests.post(url, verify=False, json=data).json()
            access_token = response.get('access_token')
            expires_in = int(response.get('expires_in'))
            redis_client.set(token_expire_key, time_now + expires_in)
            redis_client.set(access_token_key, access_token)
            RedisLock.release_mutex(lock_name)
            return access_token
        except Exception, e:
            logger.error(traceback.format_exc())
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
            logger.error(traceback.format_exc())
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', user_name, e)
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
            logger.error(traceback.format_exc())
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', user_name, e)
            return {}

    @classmethod
    def batch_send_msgs(cls, msg, user_names, from_name='lit'):
        '''
        http://docs-im.easemob.com/start/100serverintegration/50messages
        user_names suggest to less than 20 everytime
        :param user_names:
        :return:
        '''
        query_limits = 20
        url = cls.APP_URL + 'messages'
        access_token = cls.get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization': 'Bearer %s' % access_token
        }
        res = {}
        query_lsts = []
        msg = str(msg)
        if len(user_names) > query_limits:
            from ..service import AsyncCmdService
            for i in range((len(user_names) + query_limits - 1)/query_limits):
                query_lsts.append(user_names[i * query_limits: (i + 1) * query_limits])
                AsyncCmdService.push_msg(AsyncCmdService.HUANXIN_SEND, [msg, user_names[i * query_limits: (i + 1) * query_limits]])
            return {}
        else:
            query_lsts = [user_names]
        for lst in query_lsts:
            data = {
               "target_type" : "users", # users 给用户发消息。chatgroups: 给群发消息，chatrooms: 给聊天室发消息
                "target" : lst, # 注意这里需要用数组，数组长度建议不大于20，即使只有一个用户，
                # 也要用数组 ['u1']，给用户发送时数组元素是用户名，给群组发送时
                # 数组元素是groupid
                "msg" : {
                    "type" : "txt",
                    "msg" : msg #消息内容，参考[[start:100serverintegration:30chatlog|聊天记录]]里的bodies内容
                },
                "from" : from_name #表示消息发送者。无此字段Server会默认设置为"from":"admin"，有from字段但值为空串("")时请求失败
                }
            for i in range(cls.TRY_TIMES):
                try:
                    response = requests.post(url, verify=False, headers=headers, json=data).json()
                    _ = response["data"]
                    for k in _:
                        if _[k] == u'success':
                            res[k] = True
                        else:
                            logger.error('lst:%r, k:%r', lst, k)
                    break
                except Exception as e:
                    logger.error(traceback.format_exc())
                    logger.error('Error query is user online, usernames: %r, err: %r', lst, e)
                    continue
        return res

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
            logger.error(traceback.format_exc())
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
            print url, '!' * 100
            response = requests.post(url, verify=False, headers=headers, data=json.dumps({'usernames': [dest_user_name]})).json()
            print response
            assert response.get('data')[0]
            return True
        except Exception, e:
            logger.error(traceback.format_exc())
            logger.error('Error block huanxin, user_id: %r, err: %r', source_user_name, e)
            return {}

    @classmethod
    def unblock_user(cls, source_user_name, dest_user_name):
        url = cls.APP_URL + 'users/%s/blocks/users/%s' % (source_user_name, dest_user_name)

        access_token = cls.get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization': 'Bearer %s' % access_token
        }
        try:
            response = requests.delete(url, verify=False, headers=headers).json()
            assert response.get('entities')[0]['username']
            return True
        except Exception, e:
            logger.error(traceback.format_exc())
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return {}

    @classmethod
    def add_friend(cls, source_user_name, dest_user_name):
        return True
        url = cls.APP_URL + 'users/%s/contacts/users/%s' % (source_user_name, dest_user_name)

        access_token = cls.get_access_token_init()
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
            logger.error(traceback.format_exc())
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return False

    @classmethod
    def del_friend(cls, source_user_name, dest_user_name):
        return True
        url = cls.APP_URL + 'users/%s/contacts/users/%s' % (source_user_name, dest_user_name)

        access_token = cls.get_access_token_init()
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
            logger.error(traceback.format_exc())
            logger.error('Error create huanxin  add friend, user_id: %r, err: %r', source_user_name, e)
            return False


    @classmethod
    def update_nickname(cls, user_name, nickname):
        return True
        url = cls.APP_URL + 'users/%s' % user_name

        access_token = cls.get_access_token_init()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        for i in range(cls.TRY_TIMES):
            try:
                response = requests.put(url, verify=False, headers=headers, data=json.dumps({'nickname': nickname, 'username': user_name})).json()
                # print response
                assert response.get('entities')[0]['nickname']
                return True
            except Exception, e:
                # traceback.print_exc()
                logger.error(traceback.format_exc())
                logger.error('Error  huanxin update_nickname user, user_id: %r, response:%r, err: %r', user_name, response, e)
                # return {}
        return False

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
            logger.error(traceback.format_exc())
            logger.error('Error create huanxin get user, user_id: %r, err: %r', user_name, e)
            return {}


    @classmethod
    def create_user(cls, user_name, password):

        url = cls.APP_URL + 'users'

        access_token = cls.get_access_token()
        if not access_token:
            return False
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % access_token
        }
        data = {'username': user_name, 'password': password}
        try:
            response = requests.post(url, verify=False, headers=headers, json=data).json()
            # print response
            assert response.get('entities')[0]['username']
            return True
        except Exception, e:
            logger.error(traceback.format_exc())
            logger.error('!!!!!!!!!!!Error create huanxin user, user_name: %r, , response:%r, err: %r', user_name, requests.post(url, verify=False, headers=headers, json=data), e)
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
            logger.error(traceback.format_exc())
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
            logger.error(traceback.format_exc())
            logger.error('Error active huanxin, user_id: %r, err: %r', user_name, e)
            return {}

    @classmethod
    def is_user_online(cls, user_names):
        '''
        http://docs-im.easemob.com/im/server/ready/user#%E6%89%B9%E9%87%8F%E8%8E%B7%E5%8F%96%E7%94%A8%E6%88%B7%E5%9C%A8%E7%BA%BF%E7%8A%B6%E6%80%81
        user_names must be less than 100 everytime
        :param user_names:
        :return:
        '''
        query_limits = 100
        url = cls.APP_URL + 'users/batch/status'
        access_token = cls.get_access_token()
        if not access_token:
            return False
        headers = {
            'Authorization':'Bearer %s' % access_token
        }
        res = {}
        query_lsts = []
        for i in range((len(user_names) + query_limits - 1)/query_limits):
            query_lsts.append(user_names[i * query_limits: (i + 1) * query_limits])
        online_word = 'online'
        offline_word = 'offline'
        for lst in query_lsts:
            data = {"usernames": lst}
            for i in range(cls.TRY_TIMES):
                try:
                    response = requests.post(url, verify=False, headers=headers, json=data).json()
                    _ = response["data"]
                    for m in _:
                        for k in m:
                            if m[k] == online_word:
                                res[k] = True
                            elif m[k] == offline_word:
                                res[k] = False
                            else:
                                logger.error('lst:%r, m:%r, k:%r', lst, m, k)
                    break
                except Exception, e:
                    logger.error(traceback.format_exc())
                    logger.error('Error query is user online, usernames: %r, err: %r', lst, e)
                    continue
        return res


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
            logger.error(traceback.format_exc())
            logger.error('Error deactive huanxin response:%r , user_id: %r, err: %r', response, user_name, e)
            return True

    @classmethod
    def chat_msgs_by_hour(cls, YYMMDDHH):
        url = cls.APP_URL + 'chatmessages/%s' % YYMMDDHH

        access_token = cls.get_access_token()
        if not access_token:
            return {}
        headers = {
            'Content-Type':'application/json',
            'Authorization':'Bearer %s' % access_token
        }
        try:
            response = requests.get(url, verify=False, headers=headers).json()
            return response.get('data')[0]['url']
        except Exception, e:
            logger.error(traceback.format_exc())
            logger.error('Error create huanxin get user, response:%r,  err: %r', response, e)
            return ''