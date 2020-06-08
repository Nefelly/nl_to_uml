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
    UserTagService
)
from ....const import (
    MAX_TIME
)

logger = logging.getLogger(__name__)


def tags():
    data, status = UserTagService.get_tags()
    if status:
        return success(data)
    return fail(data)


@session_required
def user_tags(user_id):
    data, status = UserTagService.user_tags(user_id)
    if not status:
        return fail(data)
    return success(data)


@session_required
def ensure_tags():
    data, status = UserTagService.ensure_tags(request.user_id)
    if not status:
        return fail(data)
    return success(data)