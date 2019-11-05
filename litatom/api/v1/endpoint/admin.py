import os
import json
import logging
import time
from datetime import timedelta

from flask import (
    jsonify,
    request,
    render_template,
    current_app,
    send_file,
    Flask

)

from ...decorator import (
    admin_session_required
)

from ....util import write_data_to_xls

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
    User,
    UserAddressList
)
from ....service import (
    AdminService,
    UserMessageService,
    FirebaseService,
    FeedService,
    GlobalizationService,
    UserService,
    AlertService
)
from  ....const import (
    MAX_TIME,
    ONE_DAY,
    APP_PATH
)
logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)

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

def feeds_hq_html():
    return current_app.send_static_file('feed_hq.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

def upload_apk():
    apk = request.files.get('apk')
    f_name = 'lit.apk'
    version = request.values.get('version')
    if version:
        if not version.replace('.', '').isdigit() or '.' in [version[0], version[-1]]:
            return fail('wrong version')
        f_name = '%s.apk' % version
    apk.save(os.path.join(APP_PATH, f_name))
    return success()

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

def ban_user_by_feed(feed_id):
    ban_time = request.values.get('ban_time', '')
    ban_time = int(ban_time) if ban_time else ONE_DAY
    data, status = AdminService.ban_user_by_feed_id(feed_id, ban_time)
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


def get_user_id():
    phone = request.args.get('phone')
    target_loc = request.loc
    user_id = request.user_id
    if phone and phone.startswith('86'):
        user = User.get_by_phone(phone)
        if user:
            user_id = str(user.id)
            request.user_id = user_id
    return user_id


def change_loc():
    phone = request.args.get('phone')
    target_loc = request.loc
    user_id = request.user_id
    if phone and phone.startswith('86'):
        user = User.get_by_phone(phone)
        if user:
            user_id = str(user.id)
            request.user_id = user_id
    msg, status = GlobalizationService.change_loc(user_id, target_loc)
    if status:
        return success()
    return fail(msg)

def unban():
    UserService.unban_user(get_user_id())
    return success()


def change_avatar():
    nickname = request.args.get('nickname')
    user = User.get_by_nickname(nickname)
    if not user:
        return fail()
    user.avatar = '5a6989ec-74a2-11e9-977f-00163e02deb4'
    user.save()
    return success()


def mail_alert():
    data = request.json
    content = data.get('content', '')
    to_users = data.get('users', '')
    if not to_users:
        to_users = ['w326571@126.com', 'juzhongtian@gmail.com', '382365209@qq.com']
    AlertService.send_mail(to_users, content)
    return success({'to_users': to_users})


def download_phone():
    date = request.args.get('date')
    time_low = int(time.mktime(time.strptime(date, '%Y%m%d')))
    time_high = time_low + 3600 * 24
    name = '/data/tmp/%s.xls' % (date + request.loc)
    objs = UserAddressList.objects(create_time__gte=time_low, create_time__lte=time_high)
    res = []
    for obj in objs:
        user = User.get_by_id(obj.user_id)
        if user.country != request.loc:
            continue
        phones = json.loads(obj.to_json()["phones"])
        res += [[k, phones[k]] for k in phones]
    if not res:
        return fail('no data')
    write_data_to_xls(name, ['name', 'phone'], res)
    return send_file(name, as_attachment=True)


def msg_to_region():
    data = request.json
    region = data.get('region')
    msg = data.get('message')
    num = data.get('num', None)
    if num:
        num = int(num)
    if not region or not msg:
        return fail('lake of field')
    res = UserService.msg_to_region_users(region, msg, num)
    if res:
        return success()
    return fail()


def send_message_html():
    return render_template('send.html', regions=GlobalizationService.REGIONS), 200, {'Content-Type': 'text/html; charset=utf-8'}


def batch_insert_html():
    return render_template('batch_insert.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

def batch_insert():
    data = request.json
    fields = data.get("fields")
    table_name = data.get("table_name")
    main_key = data.get("main_key", "")
    insert_data = data.get("insert_data")
    msg, status = AdminService.batch_insert(table_name, fields, main_key, insert_data)

