# coding: utf-8
import functools
import logging
import warnings
from hendrix.conf import setting
import bson
from . import error
from flask import (
    current_app,
    g,
    request,
    jsonify,
)
from ..util import (
    time_str_by_ts,
)
from ..const import (
    ONE_DAY
)
from ..model import (
    User
)
from ..service import (
    UserService,
    AdminService,
    GlobalizationService,
    ExperimentService
)
from ..response import guest_forbidden

logger = logging.getLogger(__name__)


def _has_user_id():
    if request.user_id is None:
        return None  # 标示session验证时出现了Exception
    else:
        return bson.ObjectId.is_valid(request.user_id)


def _has_admin_username():
    if request.admin_user_name is None:
        return None  # 标示session验证时出现了Exception
    return request.admin_user_name


def set_exp(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        ExperimentService.set_exp()
        return view(*args, **kwargs)

    return wrapper


def set_exp_arg(arg=ONE_DAY):
    '''
    参考  https://blog.csdn.net/u013858731/article/details/54971762?utm_source=blogxgwz7
    一般 先 session_required 校验 再校验这个
    :param arg:
    :return:
    '''

    def _deco(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            ExperimentService.set_exp(expire=arg)
            return view(*args, **kwargs)

        return wrapper

    return _deco


def get_user_id_by_phone():
    phone = request.args.get('phone')
    user_id = request.user_id
    if phone and phone.startswith('86'):
        user = User.get_by_phone(phone)
        if user:
            user_id = str(user.id)
            request.user_id = user_id
    return user_id


def test_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if not setting.IS_DEV:
            return jsonify(error.FailedNotTest)
        get_user_id_by_phone()
        return view(*args, **kwargs)

    return wrapper


def session_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if current_app.debug:
            return view(*args, **kwargs)
        has_user_id = _has_user_id()
        if has_user_id:
            if request.is_guest:
                # 游客用户返回460
                return guest_forbidden()
            UserService.refresh_status(request.user_id)
            return view(*args, **kwargs)
        if has_user_id is None:  # 检查时发生了Exception, 报错而不登出.
            # logger.error("nnnnn-10")
            if request.forbidden_user_id:
                return jsonify(UserService.get_forbidden_error(
                    msg=GlobalizationService.get_region_word("banned_warn") % UserService.get_forbidden_time_by_uid(
                        request.user_id),
                    default_json=error.FailedUserBanned))
            return jsonify(error.FailedSession)

    return wrapper


def forbidden_session_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if current_app.debug:
            return view(*args, **kwargs)
        has_user_id = _has_user_id()
        if has_user_id:
            if request.is_guest:
                # 游客用户返回460
                return guest_forbidden()
            UserService.refresh_status(request.user_id)
            return view(*args, **kwargs)
        if has_user_id is None:  # 检查时发生了Exception, 报错而不登出.
            forbidden_user_id = request.forbidden_user_id
            if not forbidden_user_id:
                return jsonify(error.FailedSession)
            request.user_id = forbidden_user_id
            return view(*args, **kwargs)

    return wrapper


def session_finished_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if current_app.debug:
            return view(*args, **kwargs)
        has_user_id = _has_user_id()
        if has_user_id:
            user_finish_info = UserService.query_user_info_finished(request.user_id)
            if not user_finish_info:
                # logger.error("nnnnn-11")
                return jsonify(error.FailedFinishedSession)
            UserService.refresh_status(request.user_id)
            if request.is_guest:
                # 游客用户返回460
                return guest_forbidden()
            return view(*args, **kwargs)
        if has_user_id is None:  # 检查时发生了Exception, 报错而不登出.
            # logger.error("nnnnn-10")
            if request.forbidden_user_id:
                return jsonify(UserService.get_forbidden_error(
                    msg=GlobalizationService.get_region_word("banned_warn") % UserService.get_forbidden_time_by_uid(
                        request.user_id),
                    default_json=error.FailedUserBanned))
            # if request.forbidden_user_id:
            #     return jsonify(UserService.get_forbidden_error(error.FailedUserBanned))
            return jsonify(error.FailedSession)

    return wrapper


def admin_session_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if current_app.debug:
            return view(*args, **kwargs)
        has_user_id = _has_admin_username()
        if has_user_id:
            return view(*args, **kwargs)
        if has_user_id is None:  # 检查时发生了Exception, 报错而不登出.
            return jsonify(error.FailedNotAdmin)

    return wrapper


def session_required_with_guest(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if current_app.debug:
            return view(*args, **kwargs)
        has_user_id = _has_user_id()
        if has_user_id:
            return view(*args, **kwargs)
        if has_user_id is None:  # 检查时发生了Exception, 报错而不登出.
            return jsonify(error.FailedSession)

    return wrapper
