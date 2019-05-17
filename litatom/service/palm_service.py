# coding: utf-8
import time
import sys
from ..service import (
    AliOssService,
    GlobalizationService
)
sys.path.append('/data/opencv-3.3.0/build/palmprint_classification/pyboostcvconverter/build/')
import cv2
import pbcvt


palm_type = 'palm_type'
life = 'life'
wisdom = 'wisdom'
emotion = 'emotion'
fate = 'fate'
solar = 'solar'
desc = {
    GlobalizationService.REGION_TH: {
        palm_type: [],
        life: [],
        wisdom: [],
        emotion: [],
        fate: [],
        solar: []
    },
    GlobalizationService.REGION_VN: {
        palm_type: [],
        life: [],
        wisdom: [],
        emotion: [],
        fate: [],
        solar: []
    },


}

class PalmService(object):
    '''
    结果生成逻辑 https://shimo.im/mindmaps/NGIxXtpddR8F6eOb/
    代码: https://github.com/xuqingwenkk/palmprint_classification/tree/master/pyboostcvconverter
    '''

    @classmethod
    def get_type(cls, is_palm_rectangle, shorter_finger):
        if not is_palm_rectangle:
            if shorter_finger:
                return 0
            return 1
        if shorter_finger:
            return 2
        return 3

    @classmethod
    def get_life(cls, life_obvious, life_long):
        return 0

    @classmethod
    def get_wisdom(cls, wisdom_obvious, wisdom_long):
        return 0

    @classmethod
    def get_emotion(cls, emotion_obvious, emotion_wind):
        return 0

    @classmethod
    def get_fate(cls, fate_obvious):
        return 0

    @classmethod
    def get_solar(cls, solar_obvious):
        return 0

    @classmethod
    def output_res(cls, pic):
        img = AliOssService.get_binary_from_bucket(pic)
        if not img:
            return u'picture not exists', False
        f_name = '/tmp/%s' % pic
        with open(f_name, 'w') as f:
            f.write(img)
            f.close()
        img = cv2.imread(f_name)
        res = pbcvt.OutputFate(img)
        if res[0] not in [0, 1]:
            return u'what you upload is not a palm, please retry', False
        shorter_finger, is_palm_rectangle, solar_obvious, wisdom_obvious, wisdom_long, emotion_obvious, emotion_wind, \
        life_obvious, life_long, fate_obvious = tuple([True if el == 0 else False for el in res])
        palm_type_ind = cls.get_type(is_palm_rectangle, shorter_finger)
        life_ind = cls.get_life(life_obvious, life_long)
        wisdom_ind = cls.get_wisdom(wisdom_obvious, wisdom_long)
        emotion_ind = cls.get_emotion(emotion_obvious, emotion_wind)
        fate_ind = cls.get_fate(fate_obvious)
        solar_ind = cls.get_solar(solar_obvious)
        res = cls.get_res_by_inds(palm_type_ind, life_ind, wisdom_ind, emotion_ind, fate_ind, solar_ind)
        return {'data': res}, True

    @classmethod
    def get_res_by_inds(cls, palm_type_ind, life_ind, wisdom_ind, emotion_ind, fate_ind, solar_ind):
        def get_desc(raw_m, key, ind):
            lst = raw_m.get(key)
            if len(lst) > ind:
                return lst[ind]
            return u'not set yet'
        region = GlobalizationService.REGION_TH
        raw_m = desc.get(region, {})
        res = {
            palm_type: get_desc(raw_m, palm_type, palm_type_ind),
            life: get_desc(raw_m, life, life_ind),
            wisdom: get_desc(raw_m, wisdom, wisdom_ind),
            emotion: get_desc(raw_m, emotion, emotion_ind),
            fate: get_desc(raw_m, fate, fate_ind),
            solar: get_desc(raw_m, solar, solar_ind)
        }
        return res

