# coding: utf-8
"""
测试
"""
import logging

from flask import (
    jsonify,
    request
)

# from ...decorator import (
#     session_required
# )

from ...error import (
    Success,
    FailedLackOfField
)
from ....response import failure
from ..form import SmsCodeForm
from ....service import (
    SmsCodeService
)

logger = logging.getLogger(__name__)

def get_vfc_code():
    form = SmsCodeForm(data=request.json)
    if not form.validate():
        return failure(FailedLackOfField)
    zone = form.zone.data
    phone = form.phone.data

    msg, status = SmsCodeService.send_code(zone, phone)
    if status:
        return jsonify(Success)
    return jsonify({
        'success': False,
        'result': -1,
        'msg': msg
    })


def test():
    return jsonify(Success)
