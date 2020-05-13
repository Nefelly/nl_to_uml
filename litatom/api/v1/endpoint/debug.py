import logging
import datetime

from flask import (
    jsonify,
    request,
    Response
)

from hendrix.conf import setting
from ...decorator import (
    session_required,
    session_finished_required
)

from ....model import User

from ....response import (
    fail,
    success
)
from ....service import (
    DebugHelperService,
    AnoyMatchService,
    AliOssService,
    GlobalizationService,
    HuanxinService
)
from  ....key import (
    REDIS_MATCH_BEFORE_PREFIX
)

logger = logging.getLogger(__name__)


@session_required
def change_register_to_yes():
    user = User.get_by_id(request.user_id)
    user.create_time = datetime.datetime.now() - datetime.timedelta(days=1)
    user.save()
    return success(user.to_json())


def redis_status():
    if not setting.IS_DEV:
        return success()
    key = request.args.get('key')
    return success(DebugHelperService.debug_all_keys(key))


def clear_keys():
    if not setting.IS_DEV:
        return success()
    DebugHelperService.clear_keys()
    return success()


def batch_create_login():
    return success(DebugHelperService.batch_create_login())


def batch_anoy_match_start():
    return success(DebugHelperService.batch_anoy_match_start())


def del_match_before():
    if not setting.IS_DEV:
        return fail()
    DebugHelperService.del_match_before(request.user_id)
    return success(DebugHelperService.debug_all_keys(REDIS_MATCH_BEFORE_PREFIX))


def get_user_id_by_phone(phone):
    if phone and phone.startswith('86'):
        user = User.get_by_phone(phone)
        if user:
            return str(user.id)
    return None


def online_del_match_status():
    phone1 = request.args.get('phone1')
    phone2 = request.args.get('phone2')
    user_id1 = get_user_id_by_phone(phone1)
    user_id2 = get_user_id_by_phone(phone2)
    msg, status = DebugHelperService.online_del_match_status(user_id1, user_id2)
    if status:
        return success()
    return fail(msg)

def set_left_times_to_1():
    phone = request.args.get('phone')
    user_id = get_user_id_by_phone(phone)
    msg, status = DebugHelperService.set_left_times_to1(user_id)
    if status:
        return success()
    return fail(msg)


def down_log(user_id):
    fileid, status = DebugHelperService.get_user_log_file_id(user_id)
    if not status:
        return fail(fileid)
    content = AliOssService.get_binary_from_bucket(fileid)
    if not content:
        return Response('', mimetype='application/zip')  # 返回空流, 兼容错误
    return Response(content, mimetype='application/zip')


#@session_required
def query_region():
    phone = request.args.get('phone')
    user_id = request.user_id
    if not user_id:
        uid = get_user_id_by_phone(phone)
        if uid:
            request.user_id = uid
    return success({"region": GlobalizationService.get_region()})


def user_info():
    user_id = request.user_id
    from ....service import UserService
    phone = request.args.get('phone')
    if not user_id:
        if phone and phone.startswith('86'):
            user = User.get_by_phone(phone)
            if user:
                request.user_id = str(user.id)
    data, status = UserService.get_user_info(user_id, user_id)
    if not status:
        return fail(data)
    return success(data)


def test_func():
    if not setting.IS_DEV:
        return fail()
    from ....service import AnoyMatchService
    return success(AnoyMatchService.get_tips())

def chat_msg():
    time_str = request.values.get('time')
    url = HuanxinService.chat_msgs_by_hour(time_str)
    return success(url)