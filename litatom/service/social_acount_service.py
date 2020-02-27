# coding: utf-8
import urllib
import base64
import hashlib
import json
import time
import logging
import requests as rq
import traceback
from urllib2 import urlopen
import oss2
import requests as req
from google.oauth2 import id_token
from google.auth.transport import requests

from ..key import (
    REDIS_ACCESS_TOKEN,
)
from ..const import (
    ONE_HOUR,
    PLATFORM_ANDROID,
    PLATFORM_IOS
)
from ..service import (
    AliLogService,
)
from ..redis import RedisClient

redis_client = RedisClient()['lit']
logger = logging.getLogger(__name__)

rq.adapters.DEFAULT_RETRIES = 5  # 增加重连次数

# (Receive token by HTTPS POST)
# ...

class GoogleService(object):
    """
    TODO：1.无access_token申请失败保护
    https://developers.google.com/identity/sign-in/android/backend-auth
    """
    CLIENT_ID = '272687572250-i5659eubkl38ck9n17mrijl0neh7rgkc.apps.googleusercontent.com'
    CLIENT_SECRET = 'ZHDIw49zszjoNpVmzV3n6OYD'
    CODE = '4/wwHY-EekKYF1DrHN3Pu_GrsxShOZdko5ipTe-e-yqT2RBWJyc-rs7dCHiNHDTXo6HyJiXWlA5XAj13ZyTmdfxXA'
    IOS_CLIENT_ID = '787479292864-bgpar2s95tbkmjphofq23ivu0b2tdu9t.apps.googleusercontent.com'
    AC_TOKEN_EXPIRE_TIME = 3400
    ERR_INVALID_TOKEN = 'invalid token provided'

    @classmethod
    def _get_redis_key(cls):
        return REDIS_ACCESS_TOKEN

    @classmethod
    def _get_info_from_remark(cls, remark):
        from ..service import AccountService
        diamonds = int(remark['diamonds'])
        token = remark['payload']['token']
        product_id = AccountService.get_product_name_by_diamonds(diamonds)
        return token,product_id

    @classmethod
    def ensure_cache(cls, access_token):
        """把access_token缓存进redis"""
        key = cls._get_redis_key()
        redis_client.set(key, access_token)
        redis_client.expire(key, cls.AC_TOKEN_EXPIRE_TIME)

    @classmethod
    def _get_access_token(cls):
        """返回access_token，没有缓存则刷新"""
        key = cls._get_redis_key()
        if not redis_client.exists(key):
            cls._refresh_access_token()
        return redis_client.get(key)

    @classmethod
    def login_info(cls, token, platform=PLATFORM_ANDROID):
        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            client_id = cls.IOS_CLIENT_ID if platform == PLATFORM_IOS else cls.CLIENT_ID
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)

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
        except ValueError as e:
            # Invalid token
            # print e
            logger.error('log false token:%s, %s', token, e)
            return None

    @classmethod
    def url_append_param(cls, url, data):
        """把参数格式化写入url"""
        params = urllib.urlencode(data)
        real_url = url + '?%s' % params
        return real_url

    @classmethod
    def _get_access_token_init(cls, code=None):
        """
        页面访问获取code
        介绍： https://www.cnblogs.com/android-blogs/p/6380725.html?utm_source=itdadao&utm_medium=referral
        https://accounts.google.com/o/oauth2/auth?scope=https://www.googleapis.com/auth/androidpublisher&response_type=code&access_type=offline&redirect_uri=http://www.litatom.com/hello&client_id=272687572250-i5659eubkl38ck9n17mrijl0neh7rgkc.apps.googleusercontent.com&prompt=consent
        :param code:
        :return:
        """
        url = 'https://accounts.google.com/o/oauth2/token'
        redirect_uri = 'http://www.litatom.com/hello'
        datas = {
            "grant_type": "authorization_code",
            "code": "4/wwHGVxUL6wmwx75MC1bvRr1i_S0jQuj3ldhKxbO-CL1mzyPgECZS332EK9KfrEXzeO1kKIullQZC3K95Lpk4xhY" if not code else code,
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "redirect_uri": redirect_uri
        }
        real_url = cls.url_append_param(url, datas)
        response = req.post(real_url, verify=False).json()
        # response = requests.post(cls.SEND_URL, verify=False, headers=headers, json=data).json()
        return response

    @classmethod
    def _refresh_access_token(cls, code=None):
        """
        刷新access_token
        :param code:
        :return: 返回一个新令牌，json格式  "access_token" : "","token_type" : "Bearer","expires_in" : 3600,
        """
        url = 'https://accounts.google.com/o/oauth2/token'
        datas = {
            "grant_type": "refresh_token",
            "client_id": cls.CLIENT_ID,
            "client_secret": cls.CLIENT_SECRET,
            "refresh_token": '1//0egi5g_qCRpxzCgYIARAAGA4SNwF-L9IrJgqyzDZWOQ9QucaXGaoPiYv_Lr3gEcvCmK-J8X9PbD5nebLO0TiTqgxsM9CHfWy1YuE'
        }
        real_url = cls.url_append_param(url, datas)
        response = req.post(real_url, verify=False).json()
        access_token = response['access_token']
        cls.ensure_cache(access_token)

    @classmethod
    def get_order_info(cls, product_id, pay_token):
        """根据product_id和用户订单的token，返回订单详情，若为虚假token，则返回error response，没有任何正常订单返回的键"""
        url = 'https://www.googleapis.com/androidpublisher/v3/applications/com.litatom.app/purchases/products/' \
              + product_id + '/tokens/' + pay_token
        access_token = cls._get_access_token()
        data = {'access_token': access_token}
        real_url = cls.url_append_param(url, data)
        resp = req.get(real_url)
        return resp.json()

    @classmethod
    def judge_order_by_token(cls, product_id, pay_token):
        """
        根据product_id和pay_token返回订单是否被购买；
        :return: 若为False，则有可能token伪造，也有可能订单未被购买；True则订单已被购买
        """
        resp = cls.get_order_info(product_id, pay_token)
        key_str = 'purchaseState'
        if key_str in resp:
            state = resp['purchaseState']
            if state == 0 or state == 2:
                return True
        return False

    @classmethod
    def judge_order_online(cls, payload, user_id):
        """对线上交易订单进行检测，如有无效订单，实时记录日志"""
        token, product_id = cls._get_info_from_remark(payload)
        res = cls.judge_order_by_token(product_id, token)
        if not res:
            contents = [('token',token),('product_id',product_id),('user_id',user_id)]
            cls.put_invalid_log_to_ali_log(contents)
            return cls.ERR_INVALID_TOKEN,False
        return None,True

    @classmethod
    def judge_pay_inform_log(cls, log):
        """
        :param log: action为pay_inform的ali_log
        :return:一个tuple:错误信息(有效则为None)，是否为有效订单
        """
        contents = log.get_contents()
        remark = contents['remark']
        token, product_id = cls._get_info_from_remark(json.loads(remark))
        res = cls.judge_order_by_token(product_id, token)
        if res:
            return None
        user_id = contents['user_id']
        info = {'product_id': product_id, 'token': token, 'user_id': user_id}
        return info

    @classmethod
    def judge_history_pay_inform_log(cls, from_time, to_time):
        """
        判断时间区间内日志服务上订单的有效性
        :param from_time:
        :param to_time:
        :return:
        """
        resp = AliLogService.get_log_atom(project='litatomaction', logstore='litatomactionstore',
                                          query='action:pay_inform',
                                          from_time=from_time, to_time=to_time)
        for log in resp.logs:
            info = cls.judge_pay_inform_log(log)
            if info:
                contents = []
                for item in info:
                    contents.append((item, info[item]))
                cls.put_invalid_log_to_ali_log(contents)

    @classmethod
    def put_invalid_log_to_ali_log(cls, contents):
        contents.append(('action','invalid_order'))
        AliLogService.put_logs(contents=contents, project='litatomaction',logstore='litatomactionstore')


class FacebookService(object):
    """
    https://blog.csdn.net/mycwq/article/details/71308186
    """
    # APP_ID = '372877603536187'
    # APP_SECRET = '29e68240c95ceddbe0a6798400ce2f0a'
    APP_ID = '2249012795165840'
    APP_SECRET = '5d59b1c43df07c9ef2441abf19d6bfe9'
    APP_TOKEN = '%s|%s' % (APP_ID, APP_SECRET)

    @classmethod
    def _get_user_id(cls, token):
        try:
            url = 'https://graph.facebook.com/debug_token?access_token=%s&input_token=%s' % (cls.APP_TOKEN, token)
            s = rq.session()
            s.keep_alive = False  # 关闭多余连接
            response = s.get(url, verify=False).json()
            # print response
            assert response.get('data')['is_valid']
            return response.get('data', {}).get('user_id', None)
        except Exception as e:
            logger.error(traceback.format_exc())
            # traceback.print_exc()
            logger.error('Error get , token: %r, err: %r', token, e)
            return None

    @classmethod
    def _get_info(cls, fb_user_id):
        try:
            url = 'https://graph.facebook.com/%s?access_token=%s' % (fb_user_id, cls.APP_TOKEN)
            response = rq.get(url, verify=False).json()
            assert response.get('id')
            return response
        except Exception as e:
            logger.error(traceback.format_exc())
            # traceback.print_exc()
            logger.error('Error get , err: %r', e)
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
        try_times = 3
        for i in range(try_times):
            try:
                user_id = cls._get_user_id(token)
                assert user_id is not None
                return cls._get_info(user_id)
            except Exception as e:
                # Invalid token
                if i < try_times - 1:
                    time.sleep(0.3)
                    continue
                logger.error('log false token:%s, %s', token, e)
                return None
