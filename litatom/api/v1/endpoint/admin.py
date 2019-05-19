import logging

from flask import (
    jsonify,
    request,
    render_template,
    current_app

)

from ...decorator import (
    admin_session_required
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
from ....model import (
    User
)
from ....service import (
    AdminService,
    UserMessageService,
    FirebaseService,
    FeedService,
    GlobalizationService
)
from  ....const import (
    MAX_TIME,
    ONE_DAY
)
logger = logging.getLogger(__name__)

def login():
    data = request.json
    user_name = data.get('username', '')
    pwd = data.get('password', '')
    data, status = AdminService.login(user_name, pwd)
    if not status:
        return fail(data)
    return success(data)

@admin_session_required
def hello():
    return jsonify('hello')


def index():
    return current_app.send_static_file('admin.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}


def feeds_square_html():
    return current_app.send_static_file('feed_square.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}


#@admin_session_required
def query_reports():
    start_ts = request.values.get('start_ts', '')
    if start_ts:
        start_ts = int(start_ts)
    num = request.values.get('num', '')
    if num:
        num = int(num)
    dealed = request.values.get('dealed', '')
    if dealed in ['True', 'true']:
        dealed = True
    elif dealed in ['False', 'false']:
        dealed = False
    data, status = AdminService.query_reports(start_ts, num, dealed)
    if not status:
        return fail(data)
    return success(data)

#@admin_session_required
def ban_user(report_id):
    ban_time = request.values.get('ban_time', '')
    ban_time = int(ban_time) if ban_time else ONE_DAY
    data, status = AdminService.ban_user_by_report(report_id, ban_time)
    if not status:
        return fail(data)
    return success(data)


def feeds_square_for_admin():
    start_pos = request.args.get('start_pos')
    num = request.args.get('num')
    start_pos = int(start_pos) if start_pos and start_pos.isdigit() else 0
    num = int(num) if num and num.isdigit() else 10
    data = FeedService.feeds_square_for_admin(request.user_id, start_pos, num)
    if data:
        return success(data)
    return fail()

def add_hq(feed_id):
    data, status = FeedService.add_hq(feed_id)
    if status:
        return success()
    return fail(data)

def remove_from_hq(feed_id):
    data, status = FeedService.remove_from_hq(feed_id)
    if status:
        return success()
    return fail(data)

def delete_feed(feed_id):
    request.is_admin = True
    data, status = FeedService.delete_feed(request.user_id, feed_id)
    if status:
        return success()
    return fail(data)

#@admin_session_required
def reject(report_id):
    data, status = AdminService.reject_report(report_id)
    if not status:
        return fail(data)
    return success(data)

def change_loc():
    phone = request.args.get('phone')
    target_loc = request.loc
    user_id = request.user_id
    if phone and phone.startswith('86'):
        user = User.get_by_phone(phone)
        if user:
            user_id = str(user.id)
    status, msg = GlobalizationService.change_loc(user_id, target_loc)
    if status:
        return success()
    return fail(msg)

def change_avatar():
    nickname = request.args.get('nickname')
    user = User.get_by_nickname(nickname)
    user.avatar = '5a6989ec-74a2-11e9-977f-00163e02deb4'
    user.save()
    return success()