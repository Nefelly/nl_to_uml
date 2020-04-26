# coding: utf-8
import json
import time
import traceback
from copy import deepcopy
import logging
from qiniu import Auth, QiniuMacAuth, http
from ..service import (
    AliLogService
)
from ..const import (
    REVIEW_PIC,
    BLOCK_PIC
)
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
    def should_pic_block_from_file_id(cls, fileid):
        """
        如果是违规图，将返回(原因，建议)，否则返回None
        原因分为：'pulp','terror','politician','ads',目前只打开了pulp
        建议：'b':block, 'r':review
        """
        return cls.should_pic_block_from_url("http://www.litatom.com/api/sns/v1/lit/image/" + fileid)

    @classmethod
    def record_fail(cls, file_id, scenes, result):
        infos = deepcopy(scenes)
        infos['result'] = result
        infos = json.dumps(infos)
        content = [('id', file_id), ('name', 'pulb'), ('infos', infos)]
        AliLogService.put_logs(content, '', '', 'records', 'records')

    @classmethod
    def should_pic_block_from_url(cls, out_url):
        '''scenes could be ads, pulp...'''
        data = {
            "data": {
                "uri": out_url
            },
            "params": {
                "scenes": [
                    "pulp",
                    # "terror",
                    # "politician"
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
                if not res.text_body:
                    time.sleep(0.3)
                    continue
                test_res = json.loads(res.text_body)
                #print test_res
                err = test_res.get('error', '')
                if 'Rectangle invalid' in err:
                    return '', ''
                if ('invalid URI' in err or 'fetch uri failed' in err) and i <= loop_tms - 1:
                    time.sleep(0.3)
                    continue
                if 'result' not in test_res:
                    return '',''
                scenes = test_res['result']['scenes']
                # print scenes
                for r in scenes:
                    details = scenes[r].get('details', [])
                    # if details and details[0]['label'] != 'normal' and details[0]['score'] > cls.JUDGE_SCORE:
                    #     # logger.error('pic not past, url:%r, reason:%r', out_url, r)
                    #     # print r
                    #     return r
                    # print scenes
                    if details and details[0]['label'] != 'normal':
                        cls.record_fail(out_url, scenes, r)
                    if details and details[0].get('suggestion') == 'block':
                        cls.record_fail(out_url, scenes, r)
                        return r, BLOCK_PIC
                    if details and details[0].get('suggestion') == 'review':
                        return r, REVIEW_PIC
                return '', ''
            except Exception as e:
                logger.error(traceback.format_exc())
                logger.error('Error verify Qiniu, url: %r, err: %r, test_res:%r', out_url, e, test_res)
        return '', ''
