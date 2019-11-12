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
    UserService,
    UserMessageService,
    FirebaseService,
    AccountService
)
from  ....const import (
    MAX_TIME
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
            'message': data
        })
    return jsonify({
        'success': True,
        'result': 0,
        'data': data
    })


def google_login():
    token = request.json.get('token')
    data, status = UserService.google_login(token)
    if not status:
        return jsonify({
            'success': False,
            'result': -1,
            'message': data
        })
    return jsonify({
        'success': True,
        'result': 0,
        'data': data
    })


def facebook_login():
    token = request.json.get('token')
    data, status = UserService.facebook_login(token)
    if not status:
        return jsonify({
            'success': False,
            'result': -1,
            'message': data
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


@session_required
def search_user():
    nickname = request.values.get('nickname')
    # print nickname
    data, status = UserService.search_user(nickname, request.user_id)
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


@session_required
def user_messages():
    start_ts = request.args.get('start_ts')
    num = request.args.get('num')
    start_ts = int(start_ts) if start_ts and start_ts.isdigit() else MAX_TIME
    num = int(num) if num and num.isdigit() else 10
    data, status = UserMessageService.messages_by_uid(request.user_id, start_ts, num)
    if not status:
        return fail(data)
    return success(data)

@session_required
def read_message(message_id):
    data, status = UserMessageService.read_message(request.user_id, message_id)
    if not status:
        return fail(data)
    return success()

@session_required
def register_firebase():
    token = request.json.get('token')
    if not token:
        return fail()
    data, status = FirebaseService.add_token(request.user_id, token)
    if not status:
        return fail(data)
    return success()

@session_finished_required
def firebase_push():
    to_user_id = request.json.get('user_id', '')
    title = request.json.get('title', '')
    text = request.json.get('text', '')
    data, status = FirebaseService.send_to_user(request.user_id, title, text)
    if not status:
        return fail(data)
    return success()


@session_finished_required
def query_online():
    uids = request.json.get('user_ids', [])
    uids = uids[:100] + uids[-40:] if len(uids) > 140 else uids
    uids = list(set([_ for _ in uids if _]))
    data, status = UserService.uids_online(uids)
    if not status:
        return fail(data)
    return success(data)


@session_required
def account_info():
    data = AccountService.get_user_account_info(request.user_id)
    if not data:
        return fail()
    return success(data)


@session_required
def product_info():
    data, status = AccountService.get_product_info(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_required
def pay_inform():
    payload = request.json.data
    data, status = AccountService.deposit_diamonds(request.user_id, payload)
    if not status:
        return fail(data)
    return success(data)


@session_required
def buy_product():
    product = request.json.data.get("product")
    data, status = AccountService.buy_product(request.user_id, product)
    if not status:
        return fail(data)
    return success(data)