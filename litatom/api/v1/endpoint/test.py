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
    ExperimentService
)
from ...decorator import (
    set_exp,
    set_exp_arg
)
from ...error import Success

logger = logging.getLogger(__name__)
#print dir(logger)
#loghanlder = logging.FileHandler("/rdata/devlog", encoding='utf-8')
#logger.addHandler(loghanlder)


@set_exp_arg(20)
def test():
    return jsonify(ExperimentService.get_exp_value('haha'))


def hello():
    logger.error("hello, this is a mistake")
    assert False
    return render_template('hello.html', name='joey')