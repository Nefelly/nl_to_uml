# coding: utf-8
import base64
import hashlib
import json
import logging
import requests as rq
import traceback
from urllib2 import urlopen

import oss2

from ..const import ONE_HOUR

logger = logging.getLogger(__name__)

from google.oauth2 import id_token
from google.auth.transport import requests

# (Receive token by HTTPS POST)
# ...

class GoogleService(object):
    '''
    https://developers.google.com/identity/sign-in/android/backend-auth
    '''
    CLIENT_ID = '272687572250-i5659eubkl38ck9n17mrijl0neh7rgkc.apps.googleusercontent.com'
    @classmethod
    def login_info(cls, token):
        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), cls.CLIENT_ID)

            '''idinfo = {u'picture': u'https://lh6.googleusercontent.com/-k2KzgpaOHxg/AAAAAAAAAAI/AAAAAAAAAAA/ACHi3rcIYSdTEK8c7XzOKFZU07cQDA2z6Q/s96-c/photo.jpg',
            u'aud': u'272687572250-i5659eubkl38ck9n17mrijl0neh7rgkc.apps.googleusercontent.com', u'family_name': u'wang', u'iss': u'https://accounts.google.com',
            u'email_verified': True, u'name': u'yapeng wang', u'locale': u'zh-CN', u'given_name': u'yapeng', u'exp': 1553580984,
            u'azp': u'272687572250-q38h6dlnru40d39fa0cbais936r93064.apps.googleusercontent.com', u'iat': 1553577384, u'email': u'wangyapeng822@gmail.com',
             u'sub': u'104859548364407961110'}'''
            # Or, if multiple clients access the backend server:
            # idinfo = id_token.verify_oauth2_token(token, requests.Request())
            # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
            #     raise ValueError('Could not verify audience.')
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # If auth request is from a G Suite domain:
            # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
            #     raise ValueError('Wrong hosted domain.')

            # ID token is valid. Get the user's Google Account ID from the decoded token.
            # userid = idinfo['sub']
            return idinfo
        except ValueError, e:
            # Invalid token
            logger.error('log false token:%s, %s', token, e)
            return None



class FacebookService(object):
    '''
    https://blog.csdn.net/mycwq/article/details/71308186
    '''
    APP_ID = '372877603536187'
    APP_SECRET = '29e68240c95ceddbe0a6798400ce2f0a'
    APP_TOKEN = '%s|%s' % (APP_ID, APP_SECRET)

    @classmethod
    def _get_user_id(cls, token):
        try:
            url = 'https://graph.facebook.com/debug_token?access_token=%s&input_token=%s' % (cls.APP_TOKEN, token)
            response = rq.get(url, verify=False).json()
            assert response.get('data')['is_valid']
            return response.get('user_id')
        except Exception, e:
            traceback.print_exc()
            logger.error('Error get , token: %r, err: %r', token, e)
            return None

    @classmethod
    def _get_info(cls, fb_user_id):
        try:
            url = 'https://graph.facebook.com/%s?access_token=%s' % (fb_user_id, cls.APP_TOKEN)
            response = rq.get(url, verify=False).json()
            assert response.get('id')
            return response
        except Exception, e:
            traceback.print_exc()
            logger.error('Error get , token: %r, err: %r', token, e)
            return None

    @classmethod
    def login_info(cls, token):
        '''
        https://graph.facebook.com/debug_token?access_token=372877603536187|29e68240c95ceddbe0a6798400ce2f0a&
        input_token=EAAFTIVUafTsBAFEDaxP3vODkuCxbdGuxZAhpyDsKYvUUY7jJtIsauhDWyoQm2uIbToY9J07ZCMnrlpZCu0ZBlKWE
        sSHlxp99AmBZCKFE7Juo2Kf4eWdpEyS9gtO30D8Pmq7B22HJfJ8nKJCMRnD3caZCm8NVBIJ3JKjfZBZADar8niZB5JqFrZAcj4U6B
        Dcn8fQfI4XBXCaaZCekhDWhYg7BxdHE1gxyRCfQySJztzc5h71MQbqRRzlsZA9r
        :param token:
        :return:
        '''
        try:
            user_id = cls._get_user_id(token)
            assert user_id is not None
            return cls._get_info(user_id)
        except ValueError, e:
            # Invalid token
            logger.error('log false token:%s, %s', token, e)
            return None
