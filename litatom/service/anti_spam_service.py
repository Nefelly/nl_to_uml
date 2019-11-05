# coding: utf-8
import json
import time
import traceback
import logging
from ..model import SpamWord
from ..redis import RedisClient
from ..service import (
    GlobalizationService
)

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class AntiSpamService(object):
    '''
    docs :https://developer.qiniu.com/censor/api/5588/image-censor
    '''
            
    @classmethod
    def is_spam_word(cls, word):
        return DFAFilter.is_spam_word(word)


class DFAFilter(object):
    KEYWORD_CHAINS = {}
    DEFAULT_KEYWORD_CHAIN = {}
    DELIMIT = '\x00'
    NOT_REGION = True

    @classmethod
    def add(cls, keyword, region=None):
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
        # for word in [u'大傻', u'大瓜', u'神']:
        #     cls.add(word)
    
    @classmethod
    def is_spam_word(cls, word, region=None):
        word = word.lower()
        ret = []
        start = 0
        while start < len(word):
            level = cls.KEYWORD_CHAINS[region] if not cls.NOT_REGION else cls.DEFAULT_KEYWORD_CHAIN
            step_ins = 0
            for char in word[start:]:
                if char in level:
                    step_ins += 1
                    if cls.DELIMIT not in level[char]:
                        level = level[char]
                    else:
                        return True
                        # start += step_ins - 1
                        # break
                else:
                    ret.append(word[start])
                    break
            else:
                ret.append(word[start])
            start += 1
        return False
        # return ''.join(ret)


if __name__ == "__main__":
    DFAFilter.load()
    text = [u'大傻子哦', u'神仙', u'你好', u'大人', u'aกากจังc']
    # gfw = DFAFilter()
    # path = wordfilter_path
    # gfw.parse(path)
    # text = "这是一个政治方面的新闻"
    # result = gfw.filter(text)
    #
    for _ in text:
        print _, DFAFilter.is_spam_word(_)
    # print(text)
    # print(result)
    # time2 = time.time()
    # print('总共耗时：' + str(time2 - time1) + 's')