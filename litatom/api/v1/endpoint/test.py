# coding: utf-8
"""
测试
"""
import logging

from flask import (
    jsonify,
    request
)


from ...error import Success

logger = logging.getLogger(__name__)


def test():
    return jsonify(Success)
