import logging

from flask import (
    jsonify,
    request,
    render_template
)
from ....model import (
    Wording
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
from ....service import (
    StatisticService,
    ReportService,
    TrackActionService,
    FeedbackService
)

logger = logging.getLogger(__name__)



def online_user_count():
    gender = request.values.get('gender')
    count = StatisticService.get_online_cnt(gender)
    return success({'count': count})


def online_users():
    gender = request.args.get('gender', None)
    star_p = int(request.args.get('start_pos', 0))
    num = int(request.args.get('num', 1))
    if star_p < 0 or num < 1:
        return fail(u'wrong argument, start_pos and num must >= 0')
    data = StatisticService.get_online_users(gender, star_p, num)
    return success(data)

def get_wording():
    word_type = request.args.get('word_type')
    wording = Wording.get_word_type(word_type)
    return success(wording)


@session_finished_required
def report():
    user_id = request.user_id
    form = ReportForm(data=request.json)
    reason = form.reason.data
    pics = form.pics.data
    target_user_id = form.target_user_id.data
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
    status = TrackActionService.create_action(request.user_id, action, remark)
    if status:
        return success()
    return fail()


def privacy():
    return render_template('ppAndTos.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

def rules():
    return render_template('rules.html'), 200, {'Content-Type': 'text/html; charset=utf-8'}

@session_required
def action_by_user_id():
    data, status = TrackActionService.action_by_uid(request.user_id)
    if status:
        return success(data)
    return fail(data)
