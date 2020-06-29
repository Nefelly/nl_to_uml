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
    AntiSpamRateService,
    FeedService
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
    data = request.json
    FeedService.deal_video_res(data)
    # AliLogService.put_err_log({"msg": json.dumps(data)})
    return success()