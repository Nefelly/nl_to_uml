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
from ....const import (
    MAX_TIME
)
from ....service import (
    FeedService
)
from ...error import (
    FailedLackOfField
)

logger = logging.getLogger(__name__)


@session_finished_required
def create_feed():
    data = request.json
    content = data.get('content')
    pics = data.get('pics')
    if not content:
        return jsonify(FailedLackOfField)
    feed_id = FeedService.create_feed(request.user_id, content, pics)
    return success({'feed_id':feed_id})


def user_feeds(other_user_id):
    start_ts = request.arg.get('start_ts')
    num = request.arg.get('num')
    start_ts = int(start_ts) if start_ts.isdigit() else MAX_TIME
    num = int(num) if num.isdigit() else 10
    data, status = FeedService.feeds_by_userid(other_user_id, start_ts, num)
    if status:
        return success(data)
    return fail(data)


def square_feeds():
    user_id = None
    start_pos = request.arg.get('start_pos')
    num = request.arg.get('num')
    start_pos = int(start_pos) if start_pos.isdigit() else 0
    num = int(num) if num.isdigit() else 10
    data = FeedService.feeds_by_square(user_id, start_pos, num)
    if data:
        return success(data)
    return fail()


@session_finished_required
def like_feed(feed_id):
    data, status = FeedService.like_feed(request.user_id)
    if status:
        return success(data)
    return fail(data)


def comment_feed():
    pass


def feed_comments(feed_id):
    user_id = None
    data, status = FeedService.get_feed_comments(user_id, feed_id)
    if status:
        return success(data)
    return fail(data)
