# coding: utf-8
import logging
import time

from flask import request
from wtforms import (
    Form,
    StringField,
    IntegerField,
)
from wtforms.validators import (
    DataRequired,
    ValidationError,
)

from .util import Signature
from .. import const

logger = logging.getLogger(__name__)


class LitatomForm(Form):
    def validate(self, *args, **kwargs):
        res = super(LitatomForm, self).validate(*args, **kwargs)
        if not res:
            request.form_errors = self.errors
        print res
        return res


class PlatformField(StringField):
    PLATFORMS = [
        const.PLATFORM_IOS,
        const.PLATFORM_ANDROID,
    ]

    def process_formdata(self, valuelist):
        super(PlatformField, self).process_formdata(valuelist)
        platform = self.data.lower()
        if platform not in self.PLATFORMS:
            raise ValueError('invalid platform: {!r}'.format(self.data))
        self.data = platform


class TimestampField(StringField):
    def process_formdata(self, valuelist):
        super(TimestampField, self).process_formdata(valuelist)
        if self.data:
            # 转换为浮点数
            try:
                self.data = float(self.data)
            except ValueError:
                raise ValueError('Not a valid timestamp value: %s' % self.data)
        else:
            # 采用默认值
            try:
                self.data = self.default()
            except TypeError:
                self.data = self.default


class SignatureForm(LitatomForm):
    sign = StringField(validators=[DataRequired()])
    deviceId = StringField(validators=[DataRequired()])
    t = IntegerField(validators=[DataRequired()])
    platform = PlatformField(validators=[DataRequired()])

    _sign_err = ValidationError('invalid request signature')

    def __init__(self, formdata, *args, **kwargs):
        super(SignatureForm, self).__init__(formdata, *args, **kwargs)
        # 针对重复出现的参数, 只取最后一次出现的值，以确保算出的signature的一致性.
        params = formdata.to_dict(flat=False)
        for key in params:
            params[key] = params[key][-1]
        self.params = params

    def validate_sign(self, field):
        try:
            sign_obj = Signature.make(
                self.params, self.deviceId.data, self.platform.data)
        except Exception:
            logger.warning('error make signature obj', exc_info=True)
            raise self._sign_err
        if not sign_obj.validate(field.data):
            raise self._sign_err
