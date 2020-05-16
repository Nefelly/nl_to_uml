import logging
import json
from flask import (
    jsonify,
    request
)
from hendrix.conf import setting
from ...decorator import (
    session_required,
    session_finished_required,
    forbidden_session_required
)

from ...error import (
    Success,
    FailedLackOfField,
    FailedNotEnoughDiamonds
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
    AccountService,
    TrackActionService,
    GoogleService,
)

logger = logging.getLogger(__name__)


@forbidden_session_required
def account_info():
    data = AccountService.get_user_account_info(request.user_id)
    if not data:
        return fail()
    return success(data)


def product_info():
    data, status = AccountService.get_product_info(request.user_id)
    if not status:
        return fail(data)
    return success(data)


def pay_activities():
    data, status = AccountService.get_pay_activities()
    if not status:
        return fail(data)
    return success(data)


def diamond_products():
    data, status = AccountService.diamond_products()
    if not status:
        return fail(data)
    return success(data)


@forbidden_session_required
def pay_inform():
    payload = request.json
    user_id = request.user_id
    try:
        if setting.IS_DEV:
            data, status = None, True
        else:
            TrackActionService.create_action(request.user_id, 'pay_inform', None, None, json.dumps(payload))
            data, status = GoogleService.judge_order_online(payload, user_id)
    except Exception as e:
        logger.error('pay_inform error:%s', e)
        status = True
    finally:
        if not status:
            return fail(data)
        data, status = AccountService.deposit_diamonds(user_id, payload)
        if not status:
            return fail(data)
        return success(data)


@forbidden_session_required
def buy_vip():
    payload = request.json
    user_id = request.user_id
    try:
        if setting.IS_DEV:
            data, status = None, True
        else:
            TrackActionService.create_action(request.user_id, 'buy_vip', None, None, json.dumps(payload))
            data, status = GoogleService.judge_order_online(payload, user_id)
    except Exception as e:
        logger.error('pay_inform error:%s', e)
        status = True
    finally:
        if not status:
            return fail(data)
        data, status = AccountService.buy_vip(user_id, payload)
        if not status:
            return fail(data)
        return success(data)


@session_required
def deposit_by_activity():
    data = request.json
    activity = data.get('activity')
    other_info = data.get('other_info', {})
    # if not other_info:
    #     return fail(u'please request with a valid other_info')
    data, status = AccountService.deposit_by_activity(request.user_id, activity)
    if not status:
        return fail(data)
    return success(data)


@session_required
def reset_rate_by_diamonds():
    data = request.json
    activity = data.get('activity')
    other_info = data.get('other_info', '')
    data, status = AccountService.reset_by_diamonds(request.user_id, activity, other_info)
    if not status:
        return fail(data)
    return success(data)


def membership_badges():
    data, status = AccountService.membership_badges()
    if not status:
        return fail(data)
    return success(data)


@forbidden_session_required
def unban_by_diamonds():
    data, status = AccountService.unban_by_diamonds(request.forbidden_user_id)
    if not status:
        return fail(data)
    return success(data)


@session_required
def buy_product():
    product = request.json.get("product")
    data, status = AccountService.buy_product(request.user_id, product)
    if not status:
        if data == AccountService.ERR_DIAMONDS_NOT_ENOUGH:
            return jsonify(FailedNotEnoughDiamonds)
        return fail(data)
    return success(data)
