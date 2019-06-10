# coding: utf-8
"""
测试
"""
import logging

from ...decorator import (
    session_required,
    session_finished_required
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
    PalmService,
    GlobalizationService
)


logger = logging.getLogger(__name__)


def palm_query():
    pic = request.args.get('pic', '')
    if not pic:
        return fail('don\'t have a palm')
    data, status = PalmService.output_res(pic)
    if status:
        return success(data)
    return fail(data)

def share_info():
    result_id = request.values.get('result_id')
    analys_results = PalmService.get_res_by_result_id(result_id)
    return render_template('share_paml.html', analys_result=analys_results.values(), introduce=GlobalizationService.get_region_word('app_introduce')), 200, {'Content-Type': 'text/html; charset=utf-8'}