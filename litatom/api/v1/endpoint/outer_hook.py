# coding: utf-8
"""
测试
"""
import logging
import json
from flask import (
    jsonify,
    request,
    render_template
)

from ....service import (
    AliLogService,
    AntiSpamRateService
)
from ...decorator import (
    set_exp,
    set_exp_arg,
    session_required
)
from ...error import Success
from ....response import (
    success,
    fail
)

logger = logging.getLogger(__name__)


def video_check():
    # return jsonify('im ok')
    data = request.json
    AliLogService.put_err_log({"msg": json.dumps(data)})
    return success()