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
    GiftService
)
from ....const import (
    MAX_TIME
)

logger = logging.getLogger(__name__)


def gifts():
    data, status = GiftService.get_gifts()
    if status:
        return success(data)
    return fail(data)


@session_required
def received_gifts():
    num = request.num if request.num else 10
    data, status = GiftService.received_gifts(request.user_id, request.page_num, num)
    if not status:
        return fail(data)
    return success(data)
