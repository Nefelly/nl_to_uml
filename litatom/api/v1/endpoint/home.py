# coding: utf-8
import logging
import json
import zlib
import base64

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
    session_finished_required,
    forbidden_session_required
)

from ....response import (
    fail,
    success
)
from ....const import (
    APP_PATH,
    BLOCK_PIC,
    REVIEW_PIC,
    SPAM_RECORD_IM_SOURCE
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
    SpamWordCheckService,
    PicCheckService,
    ForbidActionService,
    AliOssService,
    ExperimentService,
    ActedService,
    TrackSpamRecordService
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
    import os
    version = request.values.get('version')
    f_name = 'lit.apk'
    if version:
        if not version.replace('.', '').isdigit() or '.' in [version[0], version[-1]]:
            return fail('wrong version')
        f_name = '%s.apk' % version
        apk = AliOssService.get_binary_from_bucket(f_name)
        with open(os.path.join(APP_PATH, f_name), 'w') as f:
            f.write(apk)
            f.close()
        # apk.save(os.path.join(APP_PATH, f_name))
    # return send_file(apk, attachment_filename=f_name, as_attachment=True)
    return send_from_directory(APP_PATH, f_name, as_attachment=True)


def get_wording():
    word_type = request.args.get('word_type')
    if request.ip_thailand and word_type == u'match_info':
        word_type = u'thai_wait'
    wording = Wording.get_word_type(word_type)
    return success(wording)


def get_spam_word():
    res, status = SpamWordCheckService.get_spam_words(GlobalizationService.get_region())
    if not status:
        return fail(res)
    return success(res)


@session_required
def report_spam():
    data = request.json
    if not data:
        return success()
    word = data.get('word')
    data, status = ForbidActionService.resolve_spam_word(request.user_id, word, SPAM_RECORD_IM_SOURCE)
    if not status:
        return fail(data)
    return success(data)


@session_required
def check_pic():
    """搭讪前10句和match环节的图片审查"""
    data = request.json
    user_id = request.user_id
    url = data.get('url')
    if not url:
        return success()
    reason, advice = PicCheckService.check_pic_by_url(url)
    if reason:
        if advice == BLOCK_PIC:
            data, status = ForbidActionService.resolve_block_pic(user_id, pic=url, source=SPAM_RECORD_IM_SOURCE)
        elif advice == REVIEW_PIC:
            data = 'review picture'
            status = TrackSpamRecordService.save_record(user_id,pic=url,forbid_weight=0,source=SPAM_RECORD_IM_SOURCE)
        else:
            data = 'normal picture'
            status = True
        if not status:
            return fail(data)
        return success(data)
    return success()


def settings():
    return success(UserSettingService.get_settings(request.user_id))


def check_version():
    version_now = '3.2.4'
    version = request.args.get('version', None)
    if 0 and GlobalizationService.get_region() == GlobalizationService.REGION_TH:
        message = u'กรุณาอัพเดทเวอร์ชั่น เราได้ทำการแก้ไขปัญหาส่งข้อความเรียบร้อยแล้ว ขอบคุณค่ะ'
    else:
        message = u'big update'
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
    # if not reason or not pics:
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
        FeedService.dislike_feed(user_id, feed_id, False)
        pics = feed_info['pics']
        data, status = ForbidActionService.resolve_report(user_id, reason, pics, target_user_id, feed_id)
    elif chat_record:
        data, status = ForbidActionService.resolve_report(user_id, reason, pics, target_user_id, None, None,
                                                          json.dumps(chat_record))
    else:
        data, status = ForbidActionService.resolve_report(user_id, reason, pics, target_user_id)
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
    # form = FeedbackForm(data=request.json)
    data = request.json
    content = data.get('content')
    pics = data.get('pics', [])
    phone = data.get('phone')
    if not content:
        return fail()
    data, status = FeedbackService.feedback(user_id, content, pics, phone)
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


def track_network():
    data = request.json
    if not data or not data.get("track"):
        return success()
    data = data.get("track", [])
    stream = base64.decodestring(data)
    json_data = json.loads(zlib.decompress(stream, 16 + zlib.MAX_WBITS))
    status = TrackActionService.batch_create_client_track(json_data)
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


def community_rule():
    return success({'community_rule': GlobalizationService.get_region_word('coummunity_rule')})
    # region = GlobalizationService.get_region()
    # region = region if region in ['th', 'vi', 'id'] else 'en'
    # f_name = 'community_rules_%s.html' % region
    # return render_template(f_name), 200, {'Content-Type': 'text/html; charset=utf-8'}


def experiments():
    data = ExperimentService.get_conf()
    return success(data)


@session_required
def action_by_user_id():
    data, status = TrackActionService.action_by_uid(request.user_id)
    if status:
        return success(data)
    return fail(data)


@forbidden_session_required
def report_acted():
    acts = request.json.get('acts', [])
    data, status = ActedService.report_acted(request.user_id, acts)
    if status:
        return success(data)
    return fail(data)


@forbidden_session_required
def acted_actions():
    data, status = ActedService.acted_actions(request.user_id)
    if status:
        return success(data)
    return fail(data)
