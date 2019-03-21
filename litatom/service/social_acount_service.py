# coding: utf-8
import base64
import hashlib
import json
import logging
import time
import uuid
from urllib2 import urlopen

import oss2

from ..const import ONE_HOUR

logger = logging.getLogger(__name__)

auth = oss2.Auth('LTAIxjghAKbw6DrM',  'QpvYuzO2X5QwxYaZwgpsjjkBDEYFNP')
img_bucket = oss2.Bucket(auth, 'oss-cn-hongkong-internal.aliyuncs.com', 'litatom')


from google.oauth2 import id_token
from google.auth.transport import requests

# (Receive token by HTTPS POST)
# ...

class GoogleService(object):
    '''
    https://developers.google.com/identity/sign-in/android/backend-auth
    '''
    CLIENT_ID = '272687572250-i5659eubkl38ck9n17mrijl0neh7rgkc.apps.googleusercontent.com '
    @classmethod
    def login_info(cls, token):
        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), cls.CLIENT_ID)

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
            userid = idinfo['sub']
        except ValueError:
            # Invalid token
            pass



