import logging
import json
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
    TrackActionService
)
logger = logging.getLogger(__name__)


@session_required
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
    data, status = AccountService.diamond_products(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_required
def pay_inform():
    payload = request.json
    TrackActionService.create_action(request.user_id, 'pay_inform', None, None, json.dumps(payload))
    data, status = AccountService.deposit_diamonds(request.user_id, payload)
    if not status:
        return fail(data)
    return success(data)


@session_required
def deposit_by_activity():
    data = request.json
    activity = data.get('activity')
    other_info = data.get('other_info')
    if not other_info:
        return fail(u'please request with a valid other_info')
    data, status = AccountService.deposit_by_activity(request.user_id, activity)
    if not status:
        return fail(data)
    return success(data)


def unban_by_diamonds(user_id):
    data, status = AccountService.unban_by_diamonds(user_id)
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