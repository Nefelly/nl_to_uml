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
    GlobalizationService,
    AccostService
)


logger = logging.getLogger(__name__)


@session_required
def times_left():
    data, status = AdService.times_left(request.user_id)
    if status:
        return success(data)
    return fail(data)


@session_required
def reset_accost():
    data = request.json
    data, status = AccostService.reset_accost(request.user_id, data)
    if status:
        return success(data)
    return fail(data)