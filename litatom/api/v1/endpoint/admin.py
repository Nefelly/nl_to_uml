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
    Flask,
    Response

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
    AlertService,
    JournalService,
    UserSettingService,
    AsyncCmdService,
    AccountService
)
from  ....const import (
    MAX_TIME,
    ONE_DAY,
    APP_PATH
)
logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='static')
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


def official_feed():
    return current_app.send_static_file('official_feed.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

def admin_words():
    return current_app.send_static_file('region_info.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

def get_official_feed():
    start_ts = request.args.get('start_ts')
    num = request.args.get('num')
    start_ts = int(start_ts) if start_ts and start_ts.isdigit() else MAX_TIME
    num = int(num) if num and num.isdigit() else 10
    data, status = AdminService.get_official_feed(request.user_id, start_ts, num)
    if status:
        return success(data)
    return fail()


def add_to_top(feed_id):
    data, status = AdminService.add_to_top(feed_id)
    if status:
        return success()
    return fail(data)


def remove_from_top(feed_id):
    data, status = AdminService.remove_from_top(feed_id)
    if status:
        return success()
    return fail(data)


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


def add_diamonds():
    phone = request.args.get('phone')
    if phone and phone.startswith('86'):
        user = User.get_by_phone(phone)
        if user:
            user_id = str(user.id)
            request.user_id = user_id
            payload = {
                'diamonds': 50
            }
            msg, status = AccountService.deposit_diamonds(user_id, payload)
            if status:
                return success(AccountService.get_user_account_info(user_id))
            return fail(msg)
    return fail('un aothorized')

def set_diamonds():
    phone = request.args.get('phone')
    num = request.args.get('num')
    num = int(num)
    if phone and phone.startswith('86'):
        user = User.get_by_phone(phone)
        if user:
            user_id = str(user.id)
            request.user_id = user_id
            payload = {
                'diamonds': 50
            }
            msg, status = AccountService.set_diamonds(user_id, num)
            if status:
                return success(AccountService.get_user_account_info(user_id))
            return fail(msg)
    return fail('un aothorized')


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
    res = AsyncCmdService.push_msg(AsyncCmdService.BATCH_SEND, [region, str(msg), num])
    # res = UserService.msg_to_region_users(region, msg, num)
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
    insert_data = data.get("data")
    msg, status = AdminService.batch_insert(table_name, fields, main_key, insert_data)
    if status:
        return success()
    return fail(msg)


def stat_items():
    stat_type = request.values.get("stat_type")
    data, status = JournalService.get_journal_items(stat_type)
    if status:
        return success(data)
    return fail(data)


def add_stat_item():
    data = request.json
    name = data.get("name").strip()
    table_name = data.get("table_name").strip()
    judge_field = data.get("judge_field", "").strip()
    expression = data.get("expression").strip()
    stat_type = data.get("stat_type", "business")
    msg, status = JournalService.add_stat_item(name, table_name, stat_type, judge_field, expression)
    if status:
        return success()
    return fail(msg)


def delete_stat_item(item_id):
    msg, status = JournalService.delete_stat_item(item_id)
    if status:
        return success()
    return fail(msg)


def journal_cal(item_id):
    data = JournalService.cal_by_id(item_id, False)
    if data:
        return success(data)
    return fail()


def get_log(user_id):
    msg, status = FirebaseService.command_to_user(user_id, {"type": 1000})
    if status:
        return success()
    return fail(msg)


def region_words():
    data, status = GlobalizationService.region_words()
    if status:
        return success(data)
    return fail(data)


def ban_by_uid(user_id):
    data, status = AdminService.ban_by_uid(user_id)
    if status:
        return success()
    return fail(data)


def ban_reporter(user_id):
    data, status = AdminService.ban_reporter(user_id)
    if status:
        return success()
    return fail(data)


def change_setting():
    data, status = UserSettingService.change_setting(request.json)
    if status:
        return success()
    return fail(data)


def mod_setting():
    return current_app.send_static_file('modify_settings.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}


def mongo_gen_csv():
    data = request.values
    table_name = data.get("table_name")
    query = data.get("query")
    fields = data.get("fields")
    file_name, status = AdminService.mongo_gen_csv(table_name, query, fields)
    # return success()
    if not os.path.exists(file_name):
        return fail("error file not exists")
    if status:
        return Response(open(file_name).read(), mimetype='text/csv')
        return send_file(file_name, as_attachment=True)
    else:
        return fail(file_name)


def mongo_gen_csv_page():
    return current_app.send_static_file('mongo_gen_csv.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}


def journal():
    return current_app.send_static_file('journal.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}
