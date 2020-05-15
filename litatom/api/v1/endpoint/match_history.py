import logging

from flask import (
    jsonify,
    request
)

from ...decorator import (
    session_required,
    session_finished_required
)

from ....response import (
    failure,
    fail,
    success
)
from ....service import (
    MatchHistoryService
)
from ....const import (
    MAX_TIME
)

logger = logging.getLogger(__name__)


@session_required
def send_friend_request():
    data = request.json
    other_user_id = data.get('other_user_id')
    match_success_time = data.get('match_success_time')
    data, status = MatchHistoryService.send_add_request(request.user_id, other_user_id, match_success_time)
    if not status:
        return fail(data)
    return success(data)


@session_required
def accep_friend_request():
    data = request.json
    other_user_id = data.get('other_user_id')
    match_success_time = data.get('match_success_time')
    data, status = MatchHistoryService.accept_friend_request(request.user_id, other_user_id, match_success_time)
    if not status:
        return fail(data)
    return success(data)


@session_required
def matched_history():
    page_num = request.values.get('page_num', '0')
    page_num = int(page_num) if page_num and page_num.isdigit() else 0
    num = request.values.get('num', '20')
    num = int(num) if num and num.isdigit() else 10
    data, status = MatchHistoryService.get_match_history(request.user_id, page_num, num)
    if not status:
        return fail(data)
    return success(data)


