# coding: utf-8
import re
import time
import uuid
import cPickle
from base64 import b64decode

import flask
from hendrix.conf import setting
from .util import cached_property


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

    def _get_time_ms(self):
        return int(time.time() * 1000)

    def timing_begin(self):
        self.start_at = self._get_time_ms()

    def timing_end(self):
        if not self.cost:
            self.cost = self._get_time_ms() - self.start_at

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
        return self.values.get('version')
        # ua = self.headers.get('User-Agent', '')
        # for ua_content in ua.split(' '):
        #     if ua_content.startswith('Version/'):
        #         version = ua_content[len('Version/'):].strip()
        #         return version
        # return ''

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
        if not version.replace('.', '').isdigit():
            return None
        return version

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