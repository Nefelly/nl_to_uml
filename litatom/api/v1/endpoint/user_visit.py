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
    VisitService
)
from ....const import (
    MAX_TIME
)

logger = logging.getLogger(__name__)


@session_required
def new_visited_num():
    data, status = VisitService.new_visited_num(request.user_id)
    if not status:
        return fail(data)
    return success(data)

@session_required
def all_viewed():
    data, status = VisitService.all_viewed(request.user_id)
    if not status:
        return fail(data)
    return success(data)

@session_required
def visited_list():
    page_num = request.values().get('page_num', '0')
    print page_num
    page_num = int(page_num) if page_num and page_num.isdigit() else 0
    num = request.values().get('num', '0')
    num = int(num) if num and num.isdigit() else 10
    data, status = VisitService.get_visited_list(request.user_id, page_num, num)
    if not status:
        return fail(data)
    return success(data)


