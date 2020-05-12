import os
import json
import logging
import time
from datetime import timedelta
from hendrix.conf import setting

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
    admin_session_required,
    test_required,
    get_user_id_by_phone,
    set_exp_arg,
    set_user_id_by_phone
)

from ....util import write_data_to_xls
from flask_compress import Compress
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
    PicCheckService,
    TrackSpamRecordService,
    ForbidActionService,
    FirebaseService,
    FeedService,
    GlobalizationService,
    UserService,
    EmailService,
    JournalService,
    UserSettingService,
    AsyncCmdService,
    AccountService,
    FeedbackService,
    AliOssService,
    ExperimentService
)
from ....const import (
    MAX_TIME,
    ONE_DAY,
    APP_PATH,
    ONE_WEEK,
    REVIEW_PIC,
    BLOCK_PIC,
    OFFICIAL_AVATAR
)

logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
# app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)
app.config['COMPRESS_MIN_SIZE'] = 100
app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'text/xml', 'application/json', 'application/javascript']
Compress(app)


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
    AliOssService.upload_from_binary(apk, f_name)
    # apk.save(os.path.join(APP_PATH, f_name))
    return success()


# @admin_session_required
def query_reports():
    start_ts = request.values.get('start_ts', '')
    if start_ts:
        start_ts = int(start_ts)
    num = request.values.get('num', '')
    if num:
        num = int(num)
    dealed = request.values.get('dealed', '')
    show_match = request.values.get('show_match', '')
    if dealed in ['True', 'true']:
        dealed = True
    elif dealed in ['False', 'false']:
        dealed = False
    if show_match in ['True', 'true']:
        show_match = True
    elif show_match in ['False', 'false']:
        show_match = False
    data, status = AdminService.query_reports(start_ts, num, dealed, show_match)
    if not status:
        return fail(data)
    return success(data)


# @admin_session_required
def ban_user(report_id):
    ban_time = request.values.get('ban_time', '')
    ban_time = int(ban_time) if ban_time else ONE_DAY
    data, status = AdminService.ban_user_by_report(report_id, ban_time)
    if not status:
        return fail(data)
    return success(data)


def ban_device(report_id):
    data, status = AdminService.ban_device_by_report(report_id)
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


# @admin_session_required
def reject(report_id):
    data, status = AdminService.reject_report(report_id)
    if not status:
        return fail(data)
    return success(data)


def unban_by_nickname():
    nickname = request.args.get('nickname')
    data, status = UserService.unban_by_nickname(nickname)
    if not status:
        return fail(data)
    return success(data)


def restart_test():
    if not setting.IS_DEV:
        return fail(u'you are not on test')
    import subprocess
    subprocess.Popen(
        'git pull&&sv stop devlitatom&&lsof -i:8001|awk \'{print $2}\'|xargs kill -9&&sv restart devlitatom &',
        shell=True)
    return success()


@test_required
@set_exp_arg(ONE_WEEK)
def set_exp():
    return success(ExperimentService.get_exp_value(request.experiment_name))


def change_loc():
    target_loc = request.loc
    user_id = get_user_id_by_phone()
    msg, status = GlobalizationService.change_loc(user_id, target_loc)
    if status:
        return success()
    return fail(msg)


def add_diamonds():
    user_id = get_user_id_by_phone()
    if not user_id:
        return fail('unauthorized')
    payload = {
        'diamonds': 50
    }
    msg, status = AccountService.deposit_diamonds(user_id, payload)
    if status:
        return success(AccountService.get_user_account_info(user_id))
    return fail(msg)


def set_diamonds():
    user_id = get_user_id_by_phone()
    if not user_id:
        return fail('unauthorized')
    num = request.args.get('num')
    num = int(num)
    payload = {
        'diamonds': 50
    }
    msg, status = AccountService.set_diamonds(user_id, num)
    if status:
        return success(AccountService.get_user_account_info(user_id))
    return fail(msg)


def unban():
    UserService.unban_user(get_user_id_by_phone())
    return success()


@set_user_id_by_phone
def change_to_official_avatar():
    nickname = request.args.get('nickname')
    if nickname:
        user = User.get_by_nickname(nickname)
    else:
        user = User.get_by_id(request.user_id)
    if not user:
        return fail()
    user.avatar = OFFICIAL_AVATAR
    user.save()
    return success()


def mail_alert():
    data = request.json
    content = data.get('content', '')
    to_users = data.get('users', '')
    if not to_users:
        to_users = ['w326571@126.com', 'juzhongtian@gmail.com', '382365209@qq.com']
    EmailService.send_mail(to_users, content)
    return success({'to_users': to_users})


def agent():
    from flask import send_from_directory
    import os
    url = request.json.get("url")
    tmp_name = request.json.get("name")
    add = "/tmp/tmp"
    os.system('wget \'%s\' -O %s' % (url, add))
    # apk.save(os.path.join(APP_PATH, f_name))
    # return send_file(apk, attachment_filename=f_name, as_attachment=True)
    return send_from_directory(add, add, as_attachment=True)


@test_required
def replace_image():
    # import time
    # t_start = time.time()
    image = request.files.get('image')
    if not image:
        return fail()
    fileid = request.values.get('file_id')
    fileid = AliOssService.replace_from_binary(image, fileid)
    return jsonify({
        'success': True,
        'data': {
            'fileid': fileid
        }
    })


def forbid_score():
    user_id = get_user_id_by_phone()
    if not user_id:
        return fail({'reason': 'no such user'})
    credit, res = ForbidActionService.accum_illegal_credit(user_id)
    return jsonify({
        'success': True,
        'data': {
            'forbid_credit': credit,
            'forbid': res,
        }
    })


def judge_pic():
    data = request.json
    url = data.get('url')
    if not url:
        return success()
    reason, advice = PicCheckService.check_pic_by_url(url)
    if not reason:
        return fail()
    if advice == REVIEW_PIC:
        advice = 'review'
    elif advice == BLOCK_PIC:
        advice = 'block'
    return jsonify({
        'success': True,
        'data': {
            'reason': reason,
            'advice': advice,
        }
    })


def judge_lit_pic():
    data = request.json
    url = data.get('url')
    if not url:
        return success()
    reason, advice = PicCheckService.check_pic_by_fileid(url)
    if not reason:
        return fail()
    if advice == REVIEW_PIC:
        advice = 'review'
    elif advice == BLOCK_PIC:
        advice = 'block'
    return jsonify({
        'success': True,
        'data': {
            'reason': reason,
            'advice': advice,
        }
    })


def review_pic():
    return success(TrackSpamRecordService.get_review_pic())

def review_feed():
    return success(FeedService.get_review_feed())

def block_feed(feed_id):
    data, status = ForbidActionService.resolve_review_feed(feed_id)
    if not status:
        return fail()
    return success(data)


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
    return render_template('send.html', regions=GlobalizationService.REGIONS), 200, {
        'Content-Type': 'text/html; charset=utf-8'}


def batch_insert_html():
    table_name = request.values.get('table_name', '')
    fields = request.values.get('fields', '')
    return render_template('batch_insert.html', table_name=table_name, fields=fields), 200, {
        'Content-Type': 'text/html; charset=utf-8'}


def check_batch(table_name, fields):
    if not table_name or not fields:
        return False
    return True


def batch_act():
    data = request.json
    fields = data.get("fields")
    table_name = data.get("table_name")
    main_key = data.get("main_key", "")
    insert_data = data.get("data")
    is_delete = request.values.get('is_delete', '')
    if not check_batch(table_name, fields):
        return fail()
    if is_delete in ['True', 'true']:
        is_delete = True
    else:
        is_delete = False
    msg, status = AdminService.batch_insert_or_delete(table_name, fields, main_key, insert_data, is_delete)
    if status:
        return success()
    return fail(msg)


def load_table_data():
    data = request.json
    fields = data.get("fields")
    table_name = data.get("table_name")
    query = data.get("query")
    if not check_batch(table_name, fields):
        return fail()
    data, status = AdminService.load_table_data(table_name, fields, query)
    if status:
        return success(data)
    return fail(data)


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


def feedbacks():
    start_ts = request.args.get('start_ts')
    num = request.args.get('num')
    start_ts = int(start_ts) if start_ts and start_ts.isdigit() else MAX_TIME
    num = int(num) if num and num.isdigit() else 10
    data, status = FeedbackService.feed_back_list(start_ts, num)
    if status:
        return success(data)
    return fail(data)


def feedback_page():
    return current_app.send_static_file('feedback.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}


def deal_feedback(feedback_id):
    data, status = FeedbackService.deal_feedback(feedback_id)
    if status:
        return success(data)
    return fail(data)


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
