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
    fail,
    success
)
from ....service import (
    AnoyMatchService
)

logger = logging.getLogger(__name__)


@session_finished_required
def get_fakeid():
    data, status = AnoyMatchService.create_fakeid(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def anoy_match():
    data, status = AnoyMatchService.anoy_match(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def anoy_like():
    data, status = AnoyMatchService.anoy_like(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def anoy_judge():
    user_id = request.user_id
    judge = request.json.get('judge')
    data, status = AnoyMatchService.judge(user_id, judge)
    if not status:
        return fail(data)
    return success(data)


def get_tips():
    data, status = AnoyMatchService.get_tips()
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def match_times_left():
    user_id = request.user_id
    words = AnoyMatchService.get_times_left(user_id)
    return success(words)


@session_finished_required
def quit_match():
    data, status = AnoyMatchService.quit_match(request.user_id)
    if not status:
        return fail(data)
    return success(data)