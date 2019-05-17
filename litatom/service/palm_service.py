# coding: utf-8
import time
import sys
from ..service import AliOssService
sys.path.append('/data/opencv-3.3.0/build/palmprint_classification/pyboostcvconverter/build/')
import cv2
import pbcvt

class PalmService(object):
    '''
    结果生成逻辑 https://shimo.im/mindmaps/NGIxXtpddR8F6eOb/
    代码: https://github.com/xuqingwenkk/palmprint_classification/tree/master/pyboostcvconverter
    '''
    @classmethod
    def output_res(cls, pic):
        img = AliOssService.get_binary_from_bucket(pic)
        if not img:
            return u'picture not exists', False
        # img = cv2.imread(img)
        res = pbcvt.OutputFate(img)
        return {'data': res}, True
