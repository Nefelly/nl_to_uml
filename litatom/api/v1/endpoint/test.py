# coding: utf-8
"""
测试
"""
import logging

from flask import (
    jsonify,
    request,
    render_template
)

from ....service import (
    ExperimentService,
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
#print dir(logger)
#loghanlder = logging.FileHandler("/rdata/devlog", encoding='utf-8')
#logger.addHandler(loghanlder)


@session_required
@set_exp_arg()
def test():
    return jsonify(ExperimentService.get_exp_value('haha'))

@session_required
def get_comment():
    activity = request.values.get('activity')
    data, status = AntiSpamRateService.judge_stop(request.user_id, request)
    if not status:
        return fail(data)
    return success(data)

def hello():
    logger.error("hello, this is a mistake")
    assert False
    return render_template('hello.html', name='joey')