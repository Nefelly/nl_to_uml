import logging
import sys

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
    VoiceMatchService,
    VideoMatchService
)

logger = logging.getLogger(__name__)

VIDEO_TYPE = 'video'
VOICE_TYPE = 'voice'
SOUL_TYPE = 'soul'

MATCH_TYPES = {
    'video': VIDEO_TYPE,
    'voice': VOICE_TYPE,
    'soul': SOUL_TYPE
}


FUNC_SERVICE_FUNC = {
    'get_fakeid': 'create_fakeid',
    'anoy_match': 'anoy_match',
    'anoy_like': 'anoy_like',
    'anoy_judge': 'judge',
    'get_tips': 'get_tips',
    'match_times_left': 'get_times_left',
    'quit_match': 'quit_match'
}

MATCH_TYPE_SERVICE = {
    VIDEO_TYPE: VideoMatchService,
    VOICE_TYPE: VoiceMatchService,
    SOUL_TYPE: AnoyMatchService
}

def get_match_type():
    match_type = request.args.get('match_type', '')
    return MATCH_TYPES.get(match_type, SOUL_TYPE)

def is_voice_match():
    match_type = request.args.get('match_type', '')
    return match_type == 'voice'

def get_match_func(func_name):
    match_type = get_match_type()
    service  = MATCH_TYPE_SERVICE.get(match_type)
    return getattr(service, FUNC_SERVICE_FUNC.get(func_name))


@session_finished_required
def get_fakeid():
    data, status = get_match_func(sys._getframe().f_code.co_name)(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def anoy_match():
    data, status = get_match_func(sys._getframe().f_code.co_name)(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def anoy_like():
    data, status = get_match_func(sys._getframe().f_code.co_name)(request.user_id)
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def anoy_judge():
    user_id = request.user_id
    judge = request.json.get('judge')
    data, status = get_match_func(sys._getframe().f_code.co_name)(user_id, judge)
    if not status:
        return fail(data)
    return success(data)


def get_tips():
    data, status = get_match_func(sys._getframe().f_code.co_name)()
    if not status:
        return fail(data)
    return success(data)


@session_finished_required
def match_times_left():
    words = get_match_func(sys._getframe().f_code.co_name)(request.user_id)
    return success(words)


@session_finished_required
def quit_match():
    data, status = get_match_func(sys._getframe().f_code.co_name)(request.user_id)
    if not status:
        return fail(data)
    return success(data)

def video_list():
    data = ['1FN4V_tGi4Q', 'r4boSN3PRNo', '08ve8Ude9mY']
    return success(data)