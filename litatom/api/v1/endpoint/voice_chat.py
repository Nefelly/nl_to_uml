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
    VoiceChatService
)

logger = logging.getLogger(__name__)

@session_required
def invite(target_user_id):
    data, status = VoiceChatService.invite(request.user_id, target_user_id)
    if not status:
        return fail(data)
    return success(data)

@session_required
def accept(target_user_id):
    data, status = VoiceChatService.accept(request.user_id, target_user_id)
    if not status:
        return fail(data)
    return success(data)

@session_required
def cancel():
    data, status = VoiceChatService.cancel(request.user_id)
    if not status:
        return fail(data)
    return success(data)

@session_required
def reject(target_user_id):
    data, status = VoiceChatService.reject(request.user_id, target_user_id)
    if not status:
        return fail(data)
    return success(data)


@session_required
def finish_chat():
    data, status = VoiceChatService.finish_chat(request.user_id)
    if not status:
        return fail(data)
    return success(data)
