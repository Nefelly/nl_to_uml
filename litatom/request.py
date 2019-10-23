# coding: utf-8
import re
import time
import uuid
import cPickle
from base64 import b64decode

import flask
from hendrix.conf import setting
from . import const
from .util import cached_property
from .model import User
from .service import (
    AdminService,
    Ip2AddressService,
    GlobalizationService
)

class LitatomRequest(flask.Request):
    """
    Caveat: avoid logging in @property methods, they may be called by logger, which will catch you in endless loops
    """
    #: :class:`~hendrix.context.Context`
    ctx = None

    #: request start time, set by user
    start_at = 0

    #: request cost (in ms), set by user
    cost = 0

    #: form validation errors
    form_errors = None

    #: 用于打log时获取用户ID
    # 该变量=True时，request.user/user_id等属性已经被赋值并缓存，可以安全地在logger中调用
    # 该变量=False时，尝试获取request.user/user_id等属性有可能出现异常，此时不要在logger中调用，否则有死循环的风险
    has_user_session = False

    is_guest = False

    def _get_time_ms(self):
        return int(time.time() * 1000)

    def timing_begin(self):
        self.start_at = self._get_time_ms()

    def timing_end(self):
        if not self.cost:
            self.cost = self._get_time_ms() - self.start_at

    def _get_user_id_from_redis(self, sid):
        pass
        # from .rpc import java_rus_client
        # from .rpc.serializers.base import context
        try:
                return res.userId
        except:
            return None

    @cached_property
    def platform(self):
        p = self.values.get('platform', '').lower()
        if p in [const.PLATFORM_ANDROID, const.PLATFORM_IOS]:
            return p

    @cached_property
    def is_android(self):
        return self.platform == const.PLATFORM_ANDROID

    @cached_property
    def is_ios(self):
        return self.platform == const.PLATFORM_IOS

    @cached_property
    def platform_from_ua(self):
        ua = self.headers.get('User-Agent', '')
        if 'iPhone' in ua:
            return const.PLATFORM_IOS
        elif 'Android' in ua:
            return const.PLATFORM_ANDROID

    @cached_property
    def build(self):
        """
        获取请求的版本号
        有些机器型号里会带上硬件的Build，所以需要从后往前遍历
        Dalvik/2.1.0 (Linux; U; Android 7.0; MHA-AL00 Build/HUAWEIMHA-AL00)
        Resolution/1080*1920 Version/4.22.3 Build/422004 Device/(HUAWEI;MHA-AL00)
        """
        ua = self.headers.get('User-Agent', '')
        for ua_content in reversed(ua.split(' ')):
            if ua_content.startswith('Build/'):
                build = ua_content[len('Build/'):].strip()
                try:
                    build = int(build)
                    return build
                except Exception:
                    # do not log, preventing endless loop
                    pass
        return -1

    @cached_property
    def version(self):
        ua = self.headers.get('User-Agent', '')
        for ua_content in ua.split(' '):
            if ua_content.startswith('Version/'):
                version = ua_content[len('Version/'):].strip()
                return version
        return ''

    @cached_property
    def manufactor_and_device(self):
        '''
        从user agent获取手机制造商和设备信号的信息.
        return: (manufacturer, device model)
        '''
        # User Agent形如: Version/4.10.014 Build/410014 Device/(Apple Inc.;iPhone8,1)
        # 要把Apple Inc.和iPhone8,1取出
        pattern = re.compile(r'Device/\((.*);(.*)\)')
        results = pattern.findall(self.headers.get('User-Agent', ''))
        if len(results) > 0:
            return results[0]
        else:
            return '', ''

    @cached_property
    def device_resolution(self):
        """
        从user agent获取设备分辨率信息
        :return: (short_edge, long_edge)
        """
        pattern = re.compile(r'Resolution/(\d+)\*(\d+)')
        results = pattern.findall(self.headers.get('User-Agent', ''))
        if len(results) > 0:
            short_edge, long_edge = results[0]
            try:
                short_edge, long_edge = int(short_edge), int(long_edge)
            except Exception:
                short_edge, long_edge = 0, 0
            if short_edge > long_edge:
                short_edge, long_edge = long_edge, short_edge
            return short_edge, long_edge

        return 0, 0

    @cached_property
    def on_staging(self):
        from .api import util
        return util.on_staging()

    @cached_property
    def id(self):
        return uuid.uuid4().hex

    @cached_property
    def session_id(self):
        sid = self.values.get('sid', '')
        # 校验格式
        if not sid.startswith('session.'):
            return ''
        return sid

    @cached_property
    def version(self):
        version = self.values.get('version', '')
        return version

    @cached_property
    def loc(self):
        loc = self.values.get('loc', '')
        return GlobalizationService.get_real_loc(loc)
        # return loc

    # @cached_property
    # def region(self):
    #     return GlobalizationService.get_region()

    @cached_property
    def user(self):
        pass
        # from .model import User
        #
        # user_id = self.user_id
        # if not user_id:
        #     return
        # try:
        #     user = User.get_by_id(user_id)
        # except Exception:
        #     # do not log, preventing endless loop
        #     return
        # if user:
        #     self.has_user_session = True
        # return user

    @cached_property
    def user_id(self):
        """
        这个方法有3种可能的返回值，
        1. 如果返回None，说明Session校验的时候抛exception了，这个时候不要踢出用户，简单报个错就可以
        2. 如果返回一个空字符串，说明的确是Session失效了，需要踢出用户
        3. 返回正常的UserID，校验成功
        """
        sid = self.session_id
        if not sid:
            return

        # get_user_id_by_session这个方法不会抛exception，如果该方法返回None，说明在取Cache或数据库的时候出现了exception，
        # 如果返回空字符串，则说明真的session失效了
        user_id = User.get_user_id_by_session(sid)
        if user_id:
            self.has_user_session = True
        return user_id

    @cached_property
    def admin_user_name(self):
        sid = self.session_id
        if not sid:
            return

        # get_user_id_by_session这个方法不会抛exception，如果该方法返回None，说明在取Cache或数据库的时候出现了exception，
        # 如果返回空字符串，则说明真的session失效了
        user_id = AdminService.get_user_name_by_session(sid)
        if user_id:
            self.has_user_session = True
        return user_id

    @cached_property
    def device_id(self):
        return self.values.get('deviceId')

    @cached_property
    def uuid(self):
        return self.values.get('uuid')

    @cached_property
    def shumei_fingerprint(self):
        fingerprint = self.values.get('device_fingerprint1', '')
        if len(fingerprint) == 62:
            return fingerprint
        fingerprint = self.values.get('device_fingerprint', '')
        if len(fingerprint) == 62:
            return fingerprint
        return None

    @cached_property
    def ip(self):
        ip_address = self.environ.get('HTTP_X_FORWARDED_FOR', '')
        if not ip_address:
            ip_list = list(self.access_route)
            if ip_list:
                ip_address = ip_list[0]
        return ip_address.split(',')[0].strip()

    @cached_property
    def ip_country(self):
        return Ip2AddressService.ip_country(self.ip)

    @cached_property
    def ip_thailand(self):
        return self.ip_country in [u'Thailand']

    @cached_property
    def ip_thailand_china(self):
        return  self.ip_country in [u'Thailand', u'China']

    @cached_property
    def ip_should_filter(self):
        if setting.IS_DEV:
            return False
        country, city = Ip2AddressService.ip_country_city(self.ip)
        if country in [u'United States'] or \
                (False and country == u'China' and city and city not in [u'Beijing', u'Shanghai', u'Nanjing']):
            #print country, city
            return True
        return False

    @cached_property
    def ip_full_list(self):
        """combine x-forwarded-for and client's ip to get a full ip list"""
        ip = list(self.access_route)
        if self.remote_addr and ip and ip[-1] != self.remote_addr:
            ip.append(self.remote_addr)
        return ip

    @cached_property
    def web_client_version(self):
        """
        web_api传递的客户端版本
        """
        return self.headers.get('X-Client-Version', '')

    @cached_property
    def web_client_build(self):
        """
        web_api传递的客户端build号
        """
        build = self.headers.get('X-Client-Build', '')
        try:
            build = int(build)
            return build
        except Exception:
            # do not log, preventing endless loop
            return -1

    @cached_property
    def web_client_platform(self):
        """
        web_api传递的客户端平台
        """
        platform = self.headers.get('X-Client-Platform', '').lower()
        if platform in [const.PLATFORM_ANDROID, const.PLATFORM_IOS]:
            return platform
