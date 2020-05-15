# coding: utf-8
import datetime
import time
import re
from hendrix.conf import setting
import json
import traceback
from copy import deepcopy
import logging
from qiniu import Auth, QiniuMacAuth, http
from . import GlobalizationService, AliLogService
from ..const import BLOCK_PIC, REVIEW_PIC
from litatom.model import (
    SpamWord,
    Feed,
    BlockedDevices,
    UserSetting,
    UserRecord
)
from ..redis import (
    RedisClient,
)

logger = logging.getLogger(__name__)
redis_client = RedisClient()['lit']


class ForbidCheckService(object):

    @classmethod
    def check_feed(cls, feed_id):
        feed = Feed.get_by_id(feed_id)
        word = [feed.content]
        pics = feed.pics
        res_word, res_pics = cls.check_content(word, pics)
        return res_word, res_pics

    @classmethod
    def check_chat_record(cls, chat_record):
        words, pics = cls.distinguish_pic_from_chat_record(chat_record)
        res_words, res_pics = cls.check_content(words, pics, False)
        return res_words, res_pics

    @classmethod
    def check_content(cls, words=None, pics=None, is_file_id=True):
        res_words = {}
        res_pics = {}
        if words:
            for word in words:
                if SpamWordCheckService.is_spam_word(word):
                    res_words[word] = True
        if not pics:
            return res_words, None

        if is_file_id:
            for pic in pics:
                reason, advice = PicCheckService.check_pic_by_fileid(pic)
                if reason:
                    res_pics[pic] = [reason, advice]
        else:
            for pic in pics:
                reason, advice = PicCheckService.check_pic_by_fileid(pic)
                if reason:
                    res_pics[pic] = [reason, advice]
        return res_words, res_pics

    @classmethod
    def check_unknown_source_pics(cls, pic):
        if re.search('https://', pic):
            return PicCheckService.check_pic_by_url(pic)
        return PicCheckService.check_pic_by_fileid(pic)

    @classmethod
    def distinguish_pic_from_chat_record(cls, chat_record):
        words = []
        pics = []
        for record in chat_record:
            if re.search('https://a1.easemob.com/1102190223222824/lit/chatfiles/', record):
                pics.append(record)
            else:
                words.append(record)
        return words, pics

    @classmethod
    def check_sensitive_user(cls, user_id):
        """判断用户及其设备是否是敏感设备"""
        if UserRecord.has_been_forbidden(user_id):
            return True
        return cls.check_sensitive_device(user_id)

    @classmethod
    def check_sensitive_device(cls, user_id):
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting:
            return False
        return BlockedDevices.is_device_sensitive(user_setting.uuid)


class SpamWordCheckService(object):
    KEYWORD_CHAINS = {}
    DEFAULT_KEYWORD_CHAIN = {}
    DELIMIT = '\x00'
    NOT_REGION = False

    @classmethod
    def add(cls, keyword, region=None):
        """以字典嵌套格式，将keyword的每个字母存入KEYWORD_CHAINS"""
        keyword = keyword.lower()
        chars = keyword.strip()
        if not chars:
            return
        if cls.NOT_REGION:
            level = cls.DEFAULT_KEYWORD_CHAIN
        else:
            if not cls.KEYWORD_CHAINS.get(region):
                cls.KEYWORD_CHAINS[region] = {}
            level = cls.KEYWORD_CHAINS[region]
        for i in range(len(chars)):
            if chars[i] in level:
                level = level[chars[i]]
            else:
                if not isinstance(level, dict):
                    break
                for j in range(i, len(chars)):
                    level[chars[j]] = {}
                    last_level, last_char = level, chars[j]
                    level = level[chars[j]]
                last_level[last_char] = {cls.DELIMIT: 0}
                break
        if i == len(chars) - 1:
            level[cls.DELIMIT] = 0

    @classmethod
    def load(cls):
        for region in GlobalizationService.REGIONS:
            for _ in SpamWord.get_by_region(region):
                cls.add(_.word, region)

    @classmethod
    def get_spam_word(cls, word, region=None):
        if not word:
            return False
        word = word.lower()
        ret = []
        start = 0
        while start < len(word):
            level = cls.KEYWORD_CHAINS.get(region, {}) if not cls.NOT_REGION else cls.DEFAULT_KEYWORD_CHAIN
            step_ins = 0
            hit = ''
            for char in word[start:]:
                if char in level:
                    hit += char
                    step_ins += 1
                    if cls.DELIMIT not in level[char]:
                        level = level[char]
                    else:
                        return hit
                        # return True
                else:
                    ret.append(word[start])
                    break
            else:
                ret.append(word[start])
            start += 1
        return False

    @classmethod
    def is_spam_word(cls, word, region=None, online=True):
        """从word的某个位置开始连续匹配到了一个keyword，则判定为spam_word"""
        if not word:
            return False
        if online:
            region = GlobalizationService.get_region()
        word = word.lower()
        ret = []
        start = 0
        while start < len(word):
            level = cls.KEYWORD_CHAINS.get(region, {}) if not cls.NOT_REGION else cls.DEFAULT_KEYWORD_CHAIN
            step_ins = 0
            for char in word[start:]:
                if char in level:
                    step_ins += 1
                    if cls.DELIMIT not in level[char]:
                        level = level[char]
                    else:
                        return True
                else:
                    ret.append(word[start])
                    break
            else:
                ret.append(word[start])
            start += 1
        return False

    @classmethod
    def get_spam_words(cls, region):
        lst = SpamWord.get_spam_words(region.lower())
        if not lst:
            return 'not spam words', False
        return {'spam_words': lst}, True


class PicCheckService(object):
    AK = "KRI2AE8Cedn4hmtTQQnS9RjVhXNJEyvx2MCAbLS3"
    SK = "aDQkhwOsRKwXgAFPSRcMtVoNT5F1UolZECaPIBCm"
    AUTH = QiniuMacAuth(AK, SK)
    JUDGE_SCORE = 0.93

    '''
    docs :https://developer.qiniu.com/censor/api/5588/image-censor
    '''

    @classmethod
    def check_pic_by_fileid(cls, fileid):
        """
        如果是违规图，将返回(原因，建议)，否则返回None
        原因分为：'pulp','terror','politician','ads',目前只打开了pulp
        建议：'b':block, 'r':review
        """
        return cls.check_pic_by_url("http://www.litatom.com/api/sns/v1/lit/image/" + fileid)

    @classmethod
    def record_fail(cls, file_id, scenes, result):
        infos = deepcopy(scenes)
        infos['result'] = result
        infos = json.dumps(infos)
        content = [('id', file_id), ('name', 'pulb'), ('infos', infos)]
        AliLogService.put_logs(content, '', '', 'records', 'records')

    @classmethod
    def check_pic_by_url(cls, out_url):
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
                err = test_res.get('error', '')
                if 'Rectangle invalid' in err:
                    return '', ''
                if ('invalid URI' in err or 'fetch uri failed' in err) and i <= loop_tms - 1:
                    time.sleep(0.3)
                    continue
                if 'result' not in test_res:
                    return '', ''
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


SpamWordCheckService.load()
