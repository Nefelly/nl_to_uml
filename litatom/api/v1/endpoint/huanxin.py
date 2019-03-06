import logging

from flask import (
    jsonify,
    request
)

from ...decorator import (
    session_required,
    session_finished_required
)

from ...error import (
    Success,
    FailedLackOfField
)
from ....response import (
    failure,
    fail,
    success
)
from ....service import (
    HuanxinService
)

logger = logging.getLogger(__name__)


@session_required
def get_user_info(target_user_id):
    data = HuanxinService.get_user(target_user_id)
    if not data:
        return fail()
    return success(data)