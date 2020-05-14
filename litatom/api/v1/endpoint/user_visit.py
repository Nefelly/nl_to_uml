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
    failure,
    fail,
    success
)
from ....service import (
    VisitService
)
from ....const import (
    MAX_TIME
)

logger = logging.getLogger(__name__)


@session_required
def new_visited_num():
    data, status = VisitService.new_visited_num(request.user_id)
    if not status:
        return fail(data)
    return success(data)


