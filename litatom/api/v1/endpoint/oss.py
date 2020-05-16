# coding: utf-8
"""
图片上传下载
"""
import logging
import os
import time
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
from ....response import (
    failure,
    fail
)
from ....service import (
    AliOssService,
    PicCheckService,
    DebugHelperService
)

logger = logging.getLogger(__name__)


@session_required
def upload_image_from_file():
    """
    直接上传图片到云盘
    目前只用来传实名认证图片
    """
    # import time
    # t_start = time.time()
    image = request.files.get('image')
    if not image:
        return jsonify(Failed)
    # fileid = request.values.get('file_id')
    fileid = None
    fileid = AliOssService.upload_from_binary(image, fileid)
    if not fileid:
        return jsonify(Failed)
    # url = 'http://www.litatom.com/api/sns/v1/lit/image/' + fileid
    # t_before_qiniu = time.time()
    # reason = PicCheckService.check_pic_by_url(url)
    # t_end = time.time()
    # print 'qiniu using:%r, upload using:%r, ratio:%r' % (t_end - t_before_qiniu, t_before_qiniu - t_start, (t_end - t_before_qiniu)/(t_before_qiniu - t_start))
    # if reason:
    #     return fail('the pic have vialate rule of:%s please check' % reason)
    return jsonify({
        'success': True,
        'data': {
            'fileid': fileid
        }
    })


def get_image(fileid):
    if fileid == 'null':
        return jsonify(Failed)
    content = AliOssService.get_binary_from_bucket(fileid)
    # print '-' * 100, len(content), fileid
    if not content:
        return Response('', mimetype='image/jpeg')   # 返回空图片流, 兼容错误
        #return jsonify(Failed)
    response = Response(content, mimetype='image/jpeg')
    response.headers['Cache-Control'] = 'max-age=%d' % 86400
    return response


def get_simage(fileid):
    if fileid == 'null':
        return jsonify(Failed)
    content = AliOssService.get_simage(fileid)
    # content = AliOssService.gm_resize(fileid)
    # content = AliOssService.rgba_resize(fileid)
    if not content:
        return Response('', mimetype='image/jpeg')   # 返回空图片流, 兼容错误
        #return jsonify(Failed)
    # print '*' * 100, len(content)
    response = Response(content, mimetype='image/jpeg')
    response.headers['Cache-Control'] = 'max-age=%d' % 86400
    return response


def get_gimage(fileid):
    if fileid == 'null':
        return jsonify(Failed)
    # content = AliOssService.rgba_resize(fileid)
    content = AliOssService.get_simage(fileid)
    # content = AliOssService.gm_resize(fileid)
    # print '!' * 100, len(content)
    if not content:
        return Response('', mimetype='image/jpeg')   # 返回空图片流, 兼容错误
    return Response(content, mimetype='image/jpeg')


@session_required
def upload_audio_from_file():
    """
    直接上传图片到云盘
    目前只用来传实名认证图片
    """
    audio = request.files.get('audio')
    if not audio:
        return jsonify(Failed)

    fileid = AliOssService.upload_from_binary(audio)
    if not fileid:
        return jsonify(Failed)
    return jsonify({
        'success': True,
        'data': {
            'fileid': fileid
        }
    })


def get_audio(fileid):
    if fileid == 'null':
        return jsonify(Failed)
    content = AliOssService.get_binary_from_bucket(fileid)
    if not content:
        return Response('', mimetype='audio/AMR')   # 返回空流, 兼容错误
    response = Response(content, mimetype='audio/AMR')
    response.headers['Cache-Control'] = 'max-age=%d' % 86400
    return response


@session_required
def upload_log_from_file():
    """
    直接上传图片到云盘
    目前只用来传实名认证图片
    """
    log_file = request.files.get('log')
    if not log_file:
        return jsonify(Failed)

    fileid = AliOssService.upload_from_binary(log_file)
    if not fileid:
        return jsonify(Failed)
    data, status = DebugHelperService.add_user_log(request.user_id, fileid)
    if not status:
        return fail(data)
    return jsonify({
        'success': True,
        'data': {
            'fileid': fileid
        }
    })


def get_log(fileid):
    if fileid == 'null':
        return jsonify(Failed)
    content = AliOssService.get_binary_from_bucket(fileid)
    if not content:
        return Response('', mimetype='application/zip')   # 返回空流, 兼容错误
    return Response(content, mimetype='application/zip')


def get_audio_mp3(fileid):
    """https://blog.csdn.net/pj_developer/article/details/72778792"""
    if fileid == 'null':
        return jsonify(Failed)
    content = AliOssService.get_binary_from_bucket(fileid)
    if not content:
        return Response('', mimetype='audio/x-mpeg')   # 返回空流, 兼容错误
    amr_add = '/tmp/%s.amr' % fileid
    mp3_add = '/tmp/%s.mp3' % fileid
    with open(amr_add, 'w') as f:
        f.write(content)
        f.close()
    import subprocess
    subprocess.call(['ffmpeg', '-i', amr_add, mp3_add])
    content = ''
    with open(mp3_add, 'r') as f:
        content = f.read()
        f.close()
    os.remove(amr_add)
    os.remove(mp3_add)
    response = Response(content, mimetype='audio/x-mpeg')
    response.headers['Cache-Control'] = 'max-age=%d' % 86400
    return response
