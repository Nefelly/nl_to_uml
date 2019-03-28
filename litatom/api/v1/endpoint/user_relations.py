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
from ....const import (
    MAX_TIME
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
    data, status = FollowService.follow(request.user_id, other_user_id)
    if status:
        return success()
    return fail(data)

@session_finished_required
def unfollow(other_user_id):
    data, status = FollowService.unfollow(request.user_id, other_user_id)
    if status:
        return success()
    return fail(data)

@session_finished_required
def following():
    start_ts = request.args.get('start_ts')
    num = request.args.get('num')
    start_ts = int(start_ts) if start_ts and start_ts.isdigit() else 0
    num = int(num) if num and num.isdigit() else 10
    data, status = FollowService.following(request.user_id, start_ts, num)
    if status:
        return success(data)
    return fail(data)

@session_finished_required
def follower():
    start_ts = request.args.get('start_ts')
    num = request.args.get('num')
    start_ts = int(start_ts) if start_ts and start_ts.isdigit() else 0
    num = int(num) if num and num.isdigit() else 10
    data, status = FollowService.follower(request.user_id, start_ts, num)
    if status:
        return success(data)
    return fail(data)