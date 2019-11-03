# coding: utf-8
"""
测试
"""
import logging

from ...decorator import (
    session_required
)

from ....response import (
    fail,
    success
)

logger = logging.getLogger(__name__)
from flask import (
    jsonify,
    request,
    render_template
)

from ....service import (
    AdService,
    GlobalizationService
)


logger = logging.getLogger(__name__)


@session_required
def times_left():
    data, status = AdService.times_left(request.user_id)
    if status:
        return success(data)
    return fail(data)
