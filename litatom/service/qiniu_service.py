# coding: utf-8
import json
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
    def should_pic_block_from_url(cls, url):
        data = {
            "data": {
                "uri": url
            },
            "params": {
                "scenes": [
                    "pulp",
                    "terror",
                    "politician",
                    "ads"
                ]
            }
        }
        url = 'http://ai.qiniuapi.com/v3/image/censor'
        for i in range(3):
            try:
                ret, res = http._post_with_qiniu_mac(url, data, cls.AUTH)
                # headers = {"code": res.status_code, "reqid": res.req_id, "xlog": res.x_log}
                test_res = json.loads(res.text_body)
                print test_res
                scenes = test_res['result']['scenes']
                for r in scenes:
                    details = scenes[r].get('details', {})
                    if details and details[0]['score'] > cls.JUDGE_SCORE:
                        return r
                return ''
            except Exception, e:
                traceback.print_exc()
                logger.error('Error verify Qiniu, url: %r, err: %r', url, e)

        return ''