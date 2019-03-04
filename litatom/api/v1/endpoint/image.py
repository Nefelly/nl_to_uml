# coding: utf-8
"""
图片上传下载
"""
import logging

from flask import (
    jsonify,
    request,
    #send_file,
    Response
)

from ...decorator import (
    session_required
)

from ...error import (
    Success,
    Failed,
    FailedLackOfField
)
from ....response import failure
from ....service import (
    AliOssService
)

logger = logging.getLogger(__name__)

@session_required
def upload_image_from_file():
    """
    直接上传图片到云盘
    目前只用来传实名认证图片
    """
    image = request.files.get('image')
    if not image:
        return jsonify(Failed)

    fileid = AliOssService.upload_from_binary(image)
    if not fileid:
        return jsonify(Failed)

    return jsonify({
        'success': True,
        'data': {
            'fileid': fileid
        }
    })

def get_image(fileid):

    content = AliOssService.get_binary_from_bucket(fileid)
    if not content:
        return jsonify(Failed)
    return Response(content, mimetype='image/jpeg')
