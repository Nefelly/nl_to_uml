import logging

from flask import (
    jsonify,
    request
)

from ...decorator import (
    session_required,
    session_finished_required
)

from ...error import (
    Success,
    FailedLackOfField
)
from ....response import (
    failure,
    fail,
    success
)
from ..form import (
    PhoneLoginForm
)
from ....service import (
    UserService
)

logger = logging.getLogger(__name__)
# handler = logging.FileHandler("/data/log/litatom.log")
# logger.addHandler(handler)

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


@session_required
def verify_nickname():
    nickname = request.values.get('nickname', '')
    if not nickname:
        return failure(FailedLackOfField)
    exist = UserService.verify_nickname(nickname)
    return {
        'success': True,
        'result': 0,
        'data': exist
    }


@session_required
def update_info():
    user_id = request.user_id
    data = request.json
    msg, status = UserService.update_info(user_id, data)
    if not status:
        return fail(msg)
    return success()

@session_required
def get_user_info(target_user_id):
    user_id = request.user_id
    data, status = UserService.get_user_info(user_id, target_user_id)
    if not status:
        return fail(data)
    return success(data)


def get_avatars():
    data = UserService.get_avatars()
    return success(data)


@session_required
def user_info_by_huanxinids():
    ids = request.json.get('ids')
    data, status = UserService.user_infos_by_huanxinids(ids)
    if not status:
        return fail(data)
    return success(data)