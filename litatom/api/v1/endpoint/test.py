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


from ...error import Success

logger = logging.getLogger(__name__)


def test():
    return jsonify(Success)

def hello():
    logger.info("hello, this is a mistake")
    return render_template('hello.html', name='joey')