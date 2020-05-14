import logging

from flask import (
    jsonify,
    request
)

from ...decorator import (
    session_required,
    session_finished_required,
    set_exp_arg
)

from ...error import (
    Success,
    FailedLackOfField,
    FailedUserBanned
)
from ....response import (
    failure,
    fail,
    success
)
from ..form import (
    PhoneLoginForm
)
from ....const import (
    ONE_HOUR
)
from ....service import (
    UserService,
    UserMessageService,
    FirebaseService,
    AccountService,
    AccostService,
    ConversationService,
    TokenBucketService,
    AntiSpamRateService
)
from ....const import (
    MAX_TIME
)

logger = logging.getLogger(__name__)


# handler = logging.FileHandler("/data/log/litatom.log")
# logger.addHandler(handler)

def dela_login_fail(data, status):
    '''
    封禁用户返回体
    :param data:
    :param status:
    :return:
    '''
    if not status:
        if not getattr(request, 'is_banned', False):
            return jsonify({
                'success': False,
                'result': -1,
                'message': data
            })
        return jsonify(UserService.get_forbidden_error(data, FailedUserBanned))
    return jsonify({
        'success': True,
        'result': 0,
        'data': data
    })


def phone_login():
    form = PhoneLoginForm(data=request.json)
    if not form.validate():
        return failure(FailedLackOfField)
    zone = form.zone.data
    phone = form.phone.data
    code = form.code.data
    data, status = UserService.phone_login(zone, phone, code)
    return dela_login_fail(data, status)


def google_login():
    token = request.json.get('token')
    data, status = UserService.google_login(token)
    return dela_login_fail(data, status)


def facebook_login():
    token = request.json.get('token')
    data, status = UserService.facebook_login(token)
    return dela_login_fail(data, status)


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
    UserMessageService.visit_message(target_user_id, user_id)
    if not status:
        return fail(data)
    return success(data)


@session_required
def add_conversation():
    key = 'filter_conversation:{user_id}'.format(user_id=request.user_id)
    if not TokenBucketService.get_token(key, 1, 50, 100, ONE_HOUR, 2 * ONE_HOUR):
        return success()
    data = request.json
    other_user_id = data.get('other_user_id')
    conversation_id = data.get('conversation_id')
    from_type = data.get('from_type')
    if not other_user_id or not conversation_id:
        return fail(u'lake of field')
    data, status = ConversationService.add_conversation(request.user_id, other_user_id, conversation_id, from_type)
    if not status:
        return fail(data)
    return success(data)


@session_required
def pin_conversation():
    data = request.json
    other_user_id = data.get('other_user_id')
    conversation_id = data.get('conversation_id')
    if not other_user_id or not conversation_id:
        return fail(u'lake of field')
    data, status = ConversationService.pin_conversation(request.user_id, other_user_id, conversation_id)
    if not status:
        return fail(data)
    return success(data)


@session_required
def unpin_conversation():
    data = request.json
    other_user_id = data.get('other_user_id')
    conversation_id = data.get('conversation_id')
    if not other_user_id or not conversation_id:
        return fail(u'lake of field')
    data, status = ConversationService.unpin_conversation(request.user_id, other_user_id, conversation_id)
    if not status:
        return fail(data)
    return success(data)


@session_required
def delete_conversation(conversation_id):
    data, status = ConversationService.del_conversation(request.user_id, conversation_id)
    if not status:
        return fail(data)
    return success(data)


@session_required
def get_conversations():
    data, status = ConversationService.get_conversations(request.user_id)
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


@set_exp_arg()
@session_required
def accost():
    other_user_id = request.values.get('targetId', '')
    status = AccostService.can_accost(request.user_id, other_user_id, request.session_id, request.loc, request.version)
    if not status:
        return fail()
    res = {
        'status': status
    }
    return success(res)


@set_exp_arg()
@session_required
def accost_other():
    other_user_id = request.values.get('targetId', '')
    data, status = AntiSpamRateService.judge_stop(request.user_id, AntiSpamRateService.ACCOST, other_user_id, related_protcted=True, other_protected=True)
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
    if not request.json:
        return success()
    uids = request.json.get('user_ids', [])
    uids = uids[:100] + uids[-40:] if len(uids) > 140 else uids
    uids = list(set([_ for _ in uids if _]))
    data, status = UserService.uids_online(uids)
    if not status:
        return fail(data)
    return success(data)
