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
from ..form import (
    SmsCodeForm,
    PhoneLoginForm
)
from ....service import (
    UserService
)

logger = logging.getLogger(__name__)

def phone_login():
    form = PhoneLoginForm(data=request.json)
    if not form.validate():
        return failure(FailedLackOfField)
    zone = form.zone.data
    phone = form.phone.data
    code = form.code.data
    data, status = UserService.phone_login(zone, phone, code)
    if not status:
        return jsonify({
            'success': False,
            'result': -1,
            'msg': data
        })
    return jsonify({
        'success': True,
        'result': 0,
        'data': data
    })
