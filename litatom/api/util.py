# coding: utf-8
import hashlib
import logging
import random
import re
import string
import time
import urllib

from flask import request

from ..util import cached_property
from ..const import PLATFORM_IOS, DEFAULT_QUERY_LIMIT

logger = logging.getLogger(__name__)
randomiser = random.SystemRandom()


class SignatureError(Exception):
    pass


class Signature(object):
    SIGN_PARAM_NAME = 'sign'

    def __init__(self, base_str, key):
        self.base_str = base_str
        self.key = key

    @classmethod
    def make_sign_base_str(cls, platform, params):
        base_str = u''
        params.pop(cls.SIGN_PARAM_NAME, None)
        for k, v in sorted(params.iteritems()):
            base_str += u'%s=%s' % (k, v)
        base_str = base_str.encode('utf-8')
        base_str = urllib.quote_plus(base_str)
        if platform.lower() == PLATFORM_IOS:
            base_str = base_str.replace('%7E', '~')
        return base_str

    def _generate(self):
        xor_str = ''
        i = 0
        for ch in self.base_str:
            xor_str += str(ord(ch) ^ ord(self.key[i]))
            i += 1
            i = i % (len(self.key))
        signed_str = hashlib.md5(xor_str).hexdigest()
        sign = hashlib.md5('%s%s' % (signed_str, self.key)).hexdigest()
        return sign

    @cached_property
    def sign_str(self):
        try:
            return self._generate()
        except Exception as e:
            raise SignatureError(e)

    def validate(self, sign_str):
        try:
            sign_str = str(sign_str)
            if self.sign_str != sign_str:
                logger.warning('signature mismatch (legit first): %r %r',
                               self.sign_str, sign_str)
                return False
        except Exception:
            logger.warning('error signature checking', exc_info=True)
            return False
        return True

    @classmethod
    def make(cls, params, key, platform):
        params = dict(params)
        base_str = cls.make_sign_base_str(platform, params)
        return cls(base_str, key)


def make_captcha_token(user_id):
    base_str = user_id +\
        str(time.time()) +\
        str(randomiser.randint(10000, 99999))
    return hashlib.md5(base_str).hexdigest()


def make_mobile_token():
    return 'mobile_token.%s' % ''.join(
        randomiser.choice(string.lowercase) for i in range(10))


def pagination(qs, page, size):
    skip = 0
    if page > 1:
        skip = (page - 1) * size
    limit = min(size, DEFAULT_QUERY_LIMIT)
    return qs.skip(skip).limit(limit)


def total_qs(q, filter=None):
    q = q.clone()
    filter = filter or {}
    if filter:
        q = q.filter(**filter)
    if q._document._meta.get('shard_key', None):
        res = q._document._get_collection().aggregate([
            {'$match': q._query},
            {'$group': {'_id': 'sum', 'total': {'$sum': 1}}}
        ])
        res = list(res)
        if res:
            return res[0]['total']
        return 0
    return q.count()


def get_manufactor_and_device():
    """
    从user agent获取手机制造商和设备信号的信息
    :return: (manufacturer, device model)
    """
    # User Agent形如: Version/4.10.014 Build/410014 Device/(Apple Inc.;iPhone8,1)
    # 要把Apple Inc.和iPhone8,1取出
    pattern = re.compile(r'Device/\((.*);(.*)\)')
    results = pattern.findall(request.headers.get('User-Agent', ''))
    if len(results) > 0:
        return results[0]
    else:
        return '', ''
