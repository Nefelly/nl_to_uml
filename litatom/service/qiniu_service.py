# coding: utf-8
import json
import time
import traceback
import logging
from qiniu import Auth, QiniuMacAuth, http
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class QiniuService(object):
    AK = "KRI2AE8Cedn4hmtTQQnS9RjVhXNJEyvx2MCAbLS3"
    SK = "aDQkhwOsRKwXgAFPSRcMtVoNT5F1UolZECaPIBCm"
    AUTH = QiniuMacAuth(AK, SK)
    JUDGE_SCORE = 0.93

    '''
    docs :https://developer.qiniu.com/censor/api/5588/image-censor
    '''

    @classmethod
    def should_pic_block_from_url(cls, out_url):
        '''scenes could be ads, pulp...'''
        data = {
            "data": {
                "url": out_url
            },
            "params": {
                "scenes": [
                    "pulp",
                    "terror",
                    "politician"
                ]
            }
        }
        url = 'http://ai.qiniuapi.com/v3/image/censor'
        test_res = {}
        loop_tms = 3
        for i in range(loop_tms):
            try:
                ret, res = http._post_with_qiniu_mac(url, data, cls.AUTH)
                # headers = {"code": res.status_code, "reqid": res.req_id, "xlog": res.x_log}
                test_res = json.loads(res.text_body)
                #print test_res
                if 'invalid URI' in test_res.get('error', '') and i < loop_tms - 1:
                    time.sleep(0.3)
                    continue
                scenes = test_res['result']['scenes']
                for r in scenes:
                    details = scenes[r].get('details', [])
                    if details and details[0]['label'] != 'normal' and details[0]['score'] > cls.JUDGE_SCORE:
                        logger.error('pic not past, url:%r, reason:%r', out_url)
                        return r
                return ''
            except Exception, e:
                logger.error(traceback.format_exc())
                logger.error('Error verify Qiniu, url: %r, err: %r, test_res:%r', out_url, e, test_res)
        return ''