# coding: utf-8
"""
小程序情人节活动
"""
import logging

from flask import (
    jsonify,
    request
)

# from ...decorator import (
#     session_required
# )

from ...error import Success

# from ....service import (
#     ValentineService,
#     ValentineMatchService
# )

logger = logging.getLogger(__name__)


# @session_required
# def get_status():
#     user_id = request.user_id
#     status, data = ValentineService.user_status(user_id)
#     if not status:
#         return jsonify({
#             'result': -1,
#             'success': False,
#             'msg': data
#         })
#     return jsonify({
#         'result': 0,
#         'success': True,
#         'data': data
#     })


def test():
    return jsonify(Success)
