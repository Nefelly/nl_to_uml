# coding: utf-8
import base64
import hashlib
import json
import logging
import time
import uuid
from urllib2 import urlopen
from PIL import Image as pImage
from io import BytesIO
from PIL import ImageFile
from pgmagick import Image, FilterTypes, Blob
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
            logger.error('get image_from_url failed, fileid: %s, %s', fileid, e)
        return None

    @classmethod
    def get_simage(cls, fileid):
        """https://blog.csdn.net/lafengxiaoyu/article/details/82534206"""
        obj = cls.get_binary_from_bucket(fileid)
        if not obj:
            return None
        try:
            img = pImage.open(BytesIO(obj))
            (x, y) = img.size
            x_s, y_s = cls.get_resize_size(x, y)
            # print x, y , x_s, y_s
            if x == x_s:
                return obj
            out = img.resize((x_s, y_s), pImage.ANTIALIAS)
            image_byte = BytesIO()
            out.convert('RGB').save(image_byte, format='JPEG')
            res = image_byte.getvalue()
        except:
            return obj
        return res

    @classmethod
    def get_resize_size(cls, x, y, from_gm=True):
        '''
        采用阶梯式压缩方式：
        :param x:
        :param y:
        :param from_gm:
        :return:
        '''
        first_xs = 200
        seccond_xs = 800
        max_width = 1000
        first_rate = 0.5
        seccond_rate = 0.2
        if x < first_xs:
            x_s = x
        elif x < seccond_xs:
            x_s = first_xs + (x - first_xs) * first_rate
        else:
            x_s = first_xs + (seccond_xs - first_xs) * first_rate + (x - seccond_xs) * seccond_rate
            x_s = min(x_s, max_width)
        return x_s, y * x_s / x
        # judge_x = 300
        # if from_gm:
        #     judge_x *= 2
        # if x < judge_x:
        #     return x, y
        # if x < 600:
        #     return judge_x, y * judge_x / x
        # if x < 3000:
        #     return x / 2, y / 2
        # judge_x = 1000
        # return judge_x, y * judge_x / x

    @classmethod
    def gm_resize(cls, fileid):
        '''
        https://www.iteye.com/blog/willvvv-1574883
        https://pythonhosted.org/pgmagick/cookbook.html#scaling-a-jpeg-image
        :param resize:
        :return:
        '''

        obj = cls.get_binary_from_bucket(fileid)
        try:
            blob = Blob(obj)
            im = Image(blob)
            x = im.size().width()
            y = im.size().height()
            x_s, y_s = cls.get_resize_size(x, y, True)
            if x_s == x:
                return obj
            im.quality(40)
            im.filterType(FilterTypes.SincFilter)
            # x_s, y_s = x, y
            im.scale('%dx%d' % (x_s, y_s))
            im.sharpen(1.3)
            im.write(blob)
            return blob.data
        except:
            return obj

    @classmethod
    def rgba_resize(cls, fileid):
        obj = cls.get_binary_from_bucket(fileid)
        if not obj:
            return None
        # try:
        if 1:
            img = Image.open(BytesIO(obj)).convert("RGBA")
            (x, y) = img.size
            x_s = 300  # define standard width
            if x < x_s:
                return obj
            y_s = y * x_s / x  # calc height based on standard width
            # out = img.resize((x_s, y_s), Image.ANTIALIAS)

            out = img.resize((x_s, y_s), Image.ANTIALIAS)
            image_byte = BytesIO()
            out.convert('RGB').save(image_byte, format='JPEG')
            res = image_byte.getvalue()
            #
            # qrcode_image = Image.open(qrcode).convert("RGBA")
            # qrcode_image = qrcode_image.resize(self.qrcode_size_large, Image.ANTIALIAS)
        # except:
            return res
        return res

    @classmethod
    def replace_to_small(cls, fileid, x_s=300):
        obj = cls.get_binary_from_bucket(fileid)
        if not obj:
            return None
        img = pImage.open(BytesIO(obj))
        (x, y) = img.size
        if x < x_s:
            return obj
        y_s = y * x_s / x  # calc height based on standard width
        out = img.resize((x_s, y_s), Image.ANTIALIAS)
        image_byte = BytesIO()
        out.convert('RGB').save(image_byte, format='JPEG')
        res = image_byte.getvalue()
        cls.upload_from_binary(res, fileid)
        return True