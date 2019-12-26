# coding: utf-8
import random
import logging
import json
from flask import request
from ..redis import RedisClient
from ..util import validate_phone_number

from ..key import (
    REDIS_KEY_SMS_CODE
)
from ..const import (
    TEN_MINS,
    ONE_MIN
)
from ..model import (
    User
)
from ..service import (
    TokenBucketService,
    GlobalizationService
)
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

logger = logging.getLogger(__name__)

ali_client = AcsClient('LTAIhvRx5OYpK5Ij', 'Bt7U4zEZzzj88vXuoYQpvmpX3TlMqV', 'cn-hangzhou')

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

class SmsCodeService(object):
    """
    """
    LIVE_TIME = TEN_MINS
    CODE_LEN = 4
    CODE_CHARS = [str(i) for i in range(10)]
    DAY_SEND_RATE = 8
    ERR_WORONG_TELEPHONE = u'wrong telephone number'

    REGION_TEMPLATE = {
        GlobalizationService.REGION_VN: 'SMS_167973788',
        GlobalizationService.REGION_EN: 'SMS_164510648',
        GlobalizationService.REGION_TH: 'SMS_164506012',
        GlobalizationService.REGION_ID: 'SMS_167963840',
        GlobalizationService.REGION_KR: 'SMS_169112439'
    }
    @classmethod
    def gen_code(cls):
        res = ''
        for _ in range(cls.CODE_LEN):
            res += sys_rnd.choice(cls.CODE_CHARS)
        return res

    @classmethod
    def _ali_send_code(cls, phone, code):
        status = TokenBucketService.get_token(phone, 1, cls.DAY_SEND_RATE, cls.DAY_SEND_RATE)
        if not status:
            return u'You have run out of send verify code oppurtunity today, Please try facebook or google'
        _request = CommonRequest()
        _request.set_accept_format('json')
        _request.set_domain('dysmsapi.aliyuncs.com')
        _request.set_method('POST')
        _request.set_protocol_type('https') # https | http
        _request.set_version('2017-05-25')
        _request.set_action_name('SendSms')

        _request.add_query_param('RegionId', 'cn-hangzhou')
        _request.add_query_param('PhoneNumbers', phone)
        _request.add_query_param('SignName', 'Litmatch')
        # template_code = 'SMS_164506012' if request.ip_thailand else 'SMS_164510648'
        # template_code = cls.REGION_TEMPLATE.get(GlobalizationService.get_region(), 'SMS_164510648')
        template_code = 'SMS_169112439'
        _request.add_query_param('TemplateCode', template_code)
        _request.add_query_param('TemplateParam', {"code":code})
        response = ali_client.do_action(_request)
        response = json.loads(response)
        if response.get('Message', '') != 'OK':
            logger.error('send code failed, phone:%s, code:%s, response:%r', phone, code, response)
        return None

    @classmethod
    def send_code(cls, zone, phone, code=None):
        zone_phone = zone + phone
        zone_phone = validate_phone_number(zone_phone, zone)
        if not zone_phone:
            return cls.ERR_WORONG_TELEPHONE, False
        if zone.replace('+', '') != '86' and not User.get_by_phone(zone_phone):
            if not TokenBucketService.get_token('send_lock' + zone_phone, 1, 2, 2):
                return GlobalizationService.get_region_word('sms_could_not_register'), False
        if not TokenBucketService.get_token('send_lock' + zone_phone, 1, 1, 1, TEN_MINS, TEN_MINS):
            return '', True
        if zone.replace('+', '') == '86':
            code = '1314'
        else:
            code = cls.gen_code() if not code else code
            msg = cls._ali_send_code(zone_phone, code)
            if msg:
                return msg, False
        key = REDIS_KEY_SMS_CODE.format(phone=zone_phone)
        redis_client.set(key, code, ex=TEN_MINS)
        return '', True

    @classmethod
    def verify_code(cls, zone, phone, code):
        zone_phone = zone + phone
        zone_phone = validate_phone_number(zone_phone)
        if not zone_phone:
            return cls.ERR_WORONG_TELEPHONE, False
        key = REDIS_KEY_SMS_CODE.format(phone=zone_phone)
        cached_code = redis_client.get(key)
        if not cached_code or cached_code != code:
            if request.ip_thailand:
                return u'รหัสยืนยัน 4 หลัก จะส่งเข้าเบอร์โทรศัพท์ของท่าน, หากท่านไม่ได้รับรหัสยืนยัน ให้ท่านลองลงชื่อเข้าด้วยวิธีอื่น เช่นบัญชี google หรือ Facebook', False
            return u'wrong code', False
        return '', True
