# coding: utf-8
import logging
import json

from flask import (
    jsonify,
    request,
    render_template,
    current_app
)
from ....model import (
    Wording,
    UserAddressList
)
from ..form import (
    ReportForm,
    TrackChatForm,
    TrackActionForm,
    FeedbackForm
)
from ...decorator import (
    session_required,
    session_finished_required
)

from ....response import (
    fail,
    success
)
from ....const import (
    APP_PATH
)
from ....service import (
    StatisticService,
    ReportService,
    TrackActionService,
    FeedbackService,
    GlobalizationService,
    UserFilterService,
    FeedService,
    UserSettingService,
    AntiSpamService,
    UserService,
    QiniuService
)

logger = logging.getLogger(__name__)



def online_user_count():
    gender = request.values.get('gender')
    count = StatisticService.get_online_cnt(gender)
    return success({'count': count})

def online_users():
    gender = request.args.get('gender', None)
    if GlobalizationService.get_region() in [GlobalizationService.REGION_VN, GlobalizationService.REGION_ID]:
        if not UserFilterService.is_gender_filtered(request.user_id):
            gender = None
    star_p = int(request.args.get('start_pos', 0))
    num = int(request.args.get('num', 1))
    if star_p < 0 or num < 1:
        return fail(u'wrong argument, start_pos and num must >= 0')
    data = StatisticService.get_online_users(gender, star_p, num)
    return success(data)

def first_start():
    data = request.values
    return success(data)

@session_required
def upload_address_list():
    data = request.json
    phones = data.get("phones", {})
    phones = json.dumps(phones)
    user_phone = data.get("user_phone", "")
    UserAddressList.upsert(request.user_id, phones, user_phone)
    return success()

@session_required
def get_address_list():
    data = UserAddressList.get_by_user_id(request.user_id).to_json()
    return success(data)

@session_required
def online_filter():
    limits = request.json
    age_low = limits.get('age_low', None)
    age_high = limits.get('age_high', None)
    gender_limit = limits.get('gender', '')
    is_new = limits.get('is_new', False)
    if not isinstance(is_new, bool) and is_new == u'True':
        is_new = is_new == 'True'
    data, status = UserFilterService.online_filter(request.user_id, age_low, age_high, gender_limit, is_new)
    if status:
        return success(data)
    return fail(data)

@session_required
def get_online_filter():
    data, status = UserFilterService.get_filter_by_user_id(request.user_id)
    if status:
        return success(data)
    return fail(data)

def download_app():
    from flask import send_from_directory
    version = request.values.get('version')
    f_name = 'lit.apk'
    if version:
        if not version.replace('.', '').isdigit() or '.' in [version[0], version[-1]]:
            return fail('wrong version')
        f_name = '%s.apk' % version
    return send_from_directory(APP_PATH, f_name, as_attachment=True)

def get_wording():
    word_type = request.args.get('word_type')
    if request.ip_thailand and word_type == u'match_info':
        word_type = u'thai_wait'
    wording = Wording.get_word_type(word_type)
    return success(wording)

def get_spam_word():
    res, status = AntiSpamService.get_spam_words(GlobalizationService.get_region())
    if not status:
        return fail(res)
    return success(res)


@session_required
def report_spam():
    data = request.json
    word = data.get('word')
    data, status = UserService.report_spam(request.user_id, word)
    if not status:
        return fail(data)
    return success(data)


@session_required
def check_pic():
    data = request.json
    url = data.get('url')
    if not url:
        return success()
    reason = QiniuService.should_pic_block_from_url(url)
    if reason:
        data, status = UserService.report_spam(request.user_id, url)
        if not status:
            return fail(data)
        return success(data)
    return success()


def settings():
    return success(UserSettingService.get_settings(request.user_id))


def check_version():
    version_now = '2.8.1.1'
    version = request.args.get('version', None)
    if 0 and GlobalizationService.get_region() == GlobalizationService.REGION_TH:
        message = u'กรุณาอัพเดทเวอร์ชั่น เราได้ทำการแก้ไขปัญหาส่งข้อความเรียบร้อยแล้ว ขอบคุณค่ะ'
    else:
        message = u'Some new features'
    if version < version_now:
        data = {
            'need_update': True,
            'message': message
        }
    else:
        data = {
            'need_update': False,
        }
    return success(data)


@session_finished_required
def report():
    user_id = request.user_id
    data = request.json
    chat_record = data.get('chat_record', {})
    form = ReportForm(data=request.json)
    reason = form.reason.data
    pics = form.pics.data
    feed_id = form.feed_id.data
    target_user_id = form.target_user_id.data
    #if not reason or not pics:
    # if not reason or not pics:
    #     return fail('lack of reason or picture')
    if not reason:
        return fail('lack of reason')
    if reason != 'match' and not feed_id and not pics:
        return fail('lack of reason or picture')
    if feed_id:
        feed_info, status_feed = FeedService.get_feed_info(None, feed_id)
        if not status_feed:
            return fail(feed_info)
        pics = feed_info['pics']
        data, status = ReportService.report(user_id, reason, pics, target_user_id, feed_id)
    elif chat_record:
        data, status = ReportService.report(user_id, reason, pics, target_user_id, None, json.dumps(chat_record))
    else:
        data, status = ReportService.report(user_id, reason, pics, target_user_id)
    if status:
        return success(data)
    return fail(data)


def report_info(report_id):
    data, status = ReportService.info_by_id(report_id)
    if status:
        return success(data)
    return fail(data)


@session_finished_required
def feedback():
    user_id = request.user_id
    form = FeedbackForm(data=request.json)
    content = form.content.data
    pics = form.pics.data
    if not content:
        return fail()
    data, status = FeedbackService.feedback(user_id, content, pics)
    if status:
        return success(data)
    return fail(data)


def feedback_info(feedback_id):
    data, status = FeedbackService.info_by_id(feedback_id)
    if status:
        return success(data)
    return fail(data)


@session_finished_required
def track_chat():
    form = TrackChatForm(data=request.json)
    target_user_id = form.target_user_id.data
    content = form.content.data
    data, status = StatisticService.track_chat(request.user_id, target_user_id, content)
    if status:
        return success(data)
    return fail(data)


@session_required
def track_action():
    form = TrackActionForm(data=request.json)
    action = form.action.data
    remark = form.remark.data
    other_user_id = form.other_user_id.data
    amount = form.amount.data
    status = TrackActionService.create_action(request.user_id, action, other_user_id,
                                              amount, remark, request.version)
    if status:
        return success()
    return fail()


def index():
    return current_app.send_static_file('index.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}


def privacy():
    return render_template('ppAndTos.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}


def rules():
    f_name = 'rules_%s.html' % GlobalizationService.get_region()
    return render_template(f_name), 200, {'Content-Type': 'text/html; charset=utf-8'}


@session_required
def action_by_user_id():
    data, status = TrackActionService.action_by_uid(request.user_id)
    if status:
        return success(data)
    return fail(data)
