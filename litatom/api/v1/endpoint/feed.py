import logging
import bson
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
from ..form import (
    FeedCommentForm
)
from ....service import (
    FeedService
)
from ...error import (
    FailedLackOfField
)

logger = logging.getLogger(__name__)
loghanlder = logging.FileHandler("/rdata/dev1log", encoding='utf-8')
logger.addHandler(loghanlder)

@session_finished_required
def create_feed():
    data = request.json
    content = data.get('content')
    pics = data.get('pics')
    if not content:
        return jsonify(FailedLackOfField)
    feed_id = FeedService.create_feed(request.user_id, content, pics)
    return success({'feed_id':feed_id})


@session_finished_required
def delete_feed(feed_id):
    data, status = FeedService.delete_feed(request.user_id, feed_id)
    if not status:
        return fail(data)
    return success()


def user_feeds(other_user_id):
    visitor_user_id = request.user_id
    start_ts = request.args.get('start_ts')
    num = request.args.get('num')
    start_ts = int(start_ts) if start_ts and start_ts.isdigit() else MAX_TIME
    num = int(num) if num and num.isdigit() else 10
    data, status = FeedService.feeds_by_userid(visitor_user_id, other_user_id, start_ts, num)
    if status:
        return success(data)
    return fail(data)


def feed_info(feed_id):
    data, status = FeedService.get_feed_info(request.user_id, feed_id)
    if not status:
        return fail(data)
    return success(data)


def square_feeds():
    user_id = request.user_id
    start_pos = request.args.get('start_pos')
    num = request.args.get('num')
    start_pos = int(start_pos) if start_pos and start_pos.isdigit() else 0
    num = int(num) if num and num.isdigit() else 10
    data = FeedService.feeds_by_square(user_id, start_pos, num)
    if data:
        return success(data)
    return success()


def hq_feeds():
    user_id = request.user_id
    start_pos = request.args.get('start_pos')
    num = request.args.get('num')
    start_pos = int(start_pos) if start_pos and start_pos.isdigit() else 0
    num = int(num) if num and num.isdigit() else 10
    data = FeedService.feeds_by_hq(user_id, start_pos, num)
    if data:
        return success(data)
    return success()


@session_finished_required
def like_feed(feed_id):
    data, status = FeedService.like_feed(request.user_id, feed_id)
    if status:
        return success(data)
    return fail(data)


@session_finished_required
def comment_feed(feed_id):
    form = FeedCommentForm(data=request.json)
    content = form.content.data
    comment_id = form.comment_id.data
    data, status = FeedService.comment_feed(request.user_id, feed_id, content, comment_id)
    if status:
        return success(data)
    return fail(data)


@session_finished_required
def del_comment(comment_id):
    data, status = FeedService.del_comment(request.user_id, comment_id)
    if status:
        return success(data)
    return fail(data)


def feed_comments(feed_id):
    user_id = None
    data, status = FeedService.get_feed_comments(user_id, feed_id)
    if status:
        return success(data)
    return fail(data)