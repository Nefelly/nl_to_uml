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
def quit_match():
    data, status = AnoyMatchService.quit_match(request.user_id)
    if not status:
        return fail(data)
    return success(data)