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
    set_exp
)
from ...error import Success

logger = logging.getLogger(__name__)
#print dir(logger)
#loghanlder = logging.FileHandler("/rdata/devlog", encoding='utf-8')
#logger.addHandler(loghanlder)


@set_exp
def test():
    print ExperimentService.get_exp_value('haha')
    return jsonify(request.url)


def hello():
    logger.error("hello, this is a mistake")
    assert False
    return render_template('hello.html', name='joey')