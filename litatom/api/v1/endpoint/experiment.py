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
    ExperimentService
)


logger = logging.getLogger(__name__)

'''
测试流程：
 设置实验 
 根据id获取实验值  
 修改实验设置
 获取实验值
'''


def set_experiments():
    data = request.json
    exp_name = request.values.get('exp_name')
    value_bucket_num_dict = data.get('value_buckets')
    data, status = ExperimentService.adjust_buckets(exp_name, value_bucket_num_dict)
    if status:
        return success(data)
    return fail(data)


def get_experiments():
    exp_name = request.values.get('exp_name')
    data, status = ExperimentService.buckets_for_admin(exp_name)
    if status:
        return success(data)
    return fail(data)

def delete_experiment():
    exp_name = request.values.get('exp_name')
    data, status = ExperimentService.delete_exp(exp_name)
    if status:
        return success(data)
    return fail(data)


def get_all_experiments():
    data, status = ExperimentService.get_all_experiments()
    if status:
        return success(data)
    return fail(data)


@session_required
def get_exp_value():
    exp_name = request.values.get('exp_name')
    data = ExperimentService.lit_exp_value(exp_name)
    if data:
        return success(data)
    return fail(data)
