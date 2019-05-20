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
    AnoyMatchService,
    VoiceMatchService
)

logger = logging.getLogger(__name__)

def is_voice_match():
    match_type = request.args.get('match_type', '')
    return match_type == 'voice'

@session_finished_required
def get_fakeid():
    if is_voice_match():
        data, status = VoiceMatchService.create_fakeid(request.user_id)
    else:
        data, status = AnoyMatchService.create_fakeid(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def anoy_match():
    if is_voice_match():
        data, status = VoiceMatchService.anoy_match(request.user_id)
    else:
        data, status = AnoyMatchService.anoy_match(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def anoy_like():
    if is_voice_match():
        data, status = VoiceMatchService.anoy_like(request.user_id)
    else:
        data, status = AnoyMatchService.anoy_like(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def anoy_judge():
    user_id = request.user_id
    judge = request.json.get('judge')
    if is_voice_match():
        data, status = VoiceMatchService.judge(user_id, judge)
    else:
        data, status = AnoyMatchService.judge(user_id, judge)
    if not status:
        return fail(data)
    return success(data)


def get_tips():
    if is_voice_match():
        data, status = VoiceMatchService.get_tips()
    else:
        data, status = AnoyMatchService.get_tips()
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def match_times_left():
    user_id = request.user_id
    if is_voice_match():
        words = VoiceMatchService.get_times_left(user_id)
    else:
        words = AnoyMatchService.get_times_left(user_id)
    return success(words)


@session_finished_required
def quit_match():
    print 'quit match', request.user_id
    if is_voice_match():
        data, status = VoiceMatchService.quit_match(request.user_id)
    else:
        data, status = AnoyMatchService.quit_match(request.user_id)
    if not status:
        return fail(data)
    return success(data)