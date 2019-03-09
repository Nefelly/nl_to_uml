import logging

from flask import (
    jsonify,
    request
)

from ...decorator import (
    session_finished_required
)

from ....response import (
    fail,
    success
)
from ....service import (
    BlockService,
    FollowService
)

logger = logging.getLogger(__name__)


@session_finished_required
def block(other_user_id):
    data, status = BlockService.block(request.user_id, other_user_id)
    if status:
        return success()
    return fail(data)

@session_finished_required
def unblock(other_user_id):
    data, status = BlockService.unblock(request.user_id, other_user_id)
    if status:
        return success()
    return fail(data)

@session_finished_required
def blocks():
    data, status = BlockService.blocks(request.user_id)
    if status:
        return success(data)
    return fail(data)


@session_finished_required
def follow(other_user_id):
    data, status = BlockService.follow(request.user_id, other_user_id)
    if status:
        return success()
    return fail(data)

@session_finished_required
def unfollow(other_user_id):
    data, status = BlockService.unfollow(request.user_id, other_user_id)
    if status:
        return success()
    return fail(data)

@session_finished_required
def follows():
    data, status = BlockService.follows(request.user_id)
    if status:
        return success(data)
    return fail(data)