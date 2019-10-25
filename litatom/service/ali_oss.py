# coding: utf-8
import base64
import hashlib
import json
import logging
import time
import uuid
from urllib2 import urlopen
from PIL import Image
from io import BytesIO
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import oss2


logger = logging.getLogger(__name__)

auth = oss2.Auth('LTAIxjghAKbw6DrM',  'QpvYuzO2X5QwxYaZwgpsjjkBDEYFNP')
img_bucket = oss2.Bucket(auth, 'oss-cn-hongkong-internal.aliyuncs.com', 'litatom')


class AliOssService(object):

    # @classmethod
    # def get_upload_token(cls, bucket):
    #     """
    #     客户端自行上传图片所需的token，有效期一小时
    #     :param bucket: 只支持：笔记图片、身份认证、一拍即焚
    #     :return:
    #     """
    #     appid = setting.QCLOUD_IMAGE_APPID
    #     expire_date = int(time.time()) + ONE_HOUR
    #     sign = ci_auth.get_app_sign_v2(bucket, '', expire_date)
    #     return {
    #         'appid': appid,
    #         'bucket': bucket,
    #         'sign': sign,
    #         'expire_date': expire_date,
    #     }

    @classmethod
    def upload_from_binary(cls, binary, fileid=''):
        """
        把图片二进制文件上传到万象优图
        :param binary
        :param bucket: 只支持：笔记图片、实名认证
        :param fileid
        :return 上传得到的图片fileid
    """
        if not fileid:
            # 生成fileid，检查是否唯一
            while True:
                fileid = str(uuid.uuid1())
                try:
                    img_bucket.head_object(fileid)
                except Exception:
                    # 出错表示该fileid不存在
                    break
        try:
            result = img_bucket.put_object(fileid, binary)
            if result:
                return fileid
        except Exception, e:
            logger.error('upload_from_binary failed,  %s',  e)

        return ''

    @classmethod
    def upload_from_url(cls, url, bucket, fileid=''):
        """
        把url指定的图片上传到阿里云
        """
        try:
            binary = urlopen(url, timeout=3).read()
            return cls.upload_image_from_binary(binary, bucket, fileid=fileid)
        except Exception, e:
            logger.error('upload_from_url failed, url: %s, %s', url, e)

        return ''

    @classmethod
    def get_binary_from_bucket(cls, fileid):
        try:
            return img_bucket.get_object(fileid).read()
        except Exception, e:
            logger.error(' get image_from_url failed, fileid: %s, %s', fileid, e)
        return None

    @classmethod
    def get_simage(cls, fileid):
        """https://blog.csdn.net/lafengxiaoyu/article/details/82534206"""
        obj = cls.get_binary_from_bucket(fileid)
        if not obj:
            return None
        img = Image.open(BytesIO(obj))
        (x, y) = img.size
        x_s = 350  # define standard width
        if x < x_s:
            return obj
        y_s = y * x_s / x  # calc height based on standard width
        out = img.resize((x_s, y_s), Image.ANTIALIAS)
        image_byte = BytesIO()
        out.convert('RGB').save(image_byte, format='JPEG')
        res = image_byte.getvalue()
        return res
