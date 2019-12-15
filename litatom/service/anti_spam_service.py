# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    SpamWord,
    TrackSpamRecord,
    UserAction
)
from ..redis import RedisClient
from ..service import (
    GlobalizationService
)
from ..key import (
    REDIS_ACCOST_RATE,
    REDIS_ACCOST_STOP_RATE
)
from ..const import (
    ONE_MIN,
    ACTION_ACCOST_OVER,
    ACTION_ACCOST_STOP
)

logger = logging.getLogger(__name__)
redis_client = RedisClient()['lit']


class AntiSpamService(object):
    '''
    docs :https://developer.qiniu.com/censor/api/5588/image-censor
    '''
    ACCOST_PASS = 'pass'
    ACCOST_BAN = 'ban'
    ACCOST_NEED_VIDEO = 'need_video'
    ACCOST_INTER = 5 * ONE_MIN
    ACCOST_RATE = 5
    ACCOST_STOP_INTER = 10 * ONE_MIN
    ACCOST_STOP_RATE = 20


    @classmethod
    def is_spam_word(cls, word, user_id):
        is_spam = DFAFilter.is_spam_word(word)
        if is_spam:
            TrackSpamRecord.create(word, user_id)
        return is_spam

    @classmethod
    def can_accost(cls, user_id):
        def should_stop():
            stop_key = REDIS_ACCOST_STOP_RATE.format(user_id=user_id)
            stop_num = redis_client.get(stop_key)
            if not stop_num:
                redis_client.set(stop_key, cls.ACCOST_STOP_RATE - 1, cls.ACCOST_STOP_INTER)
                return False
            else:
                stop_num = int(stop_num)
                if stop_num <= 0:
                    UserAction.create(user_id, ACTION_ACCOST_STOP, None, None, ACTION_ACCOST_STOP)
                    return True
                redis_client.decr(stop_key)
                return False
        key = REDIS_ACCOST_RATE.format(user_id=user_id)
        rate = cls.ACCOST_RATE - 1   # the first time is used
        res = redis_client.get(key)
        if not res:
            if should_stop():
                return cls.ACCOST_BAN
            redis_client.set(key, rate, cls.ACCOST_INTER)
            return cls.ACCOST_PASS
        else:
            if should_stop():
                return cls.ACCOST_BAN
            res = int(res)
            if res <= 0:
                UserAction.create(user_id, ACTION_ACCOST_OVER, None, None, ACTION_ACCOST_OVER)
                return cls.ACCOST_NEED_VIDEO
            else:
                redis_client.decr(key)
                return cls.ACCOST_PASS

    @classmethod
    def reset_accost(cls, user_id, data):
        key = REDIS_ACCOST_RATE.format(user_id=user_id)
        redis_client.set(key, cls.ACCOST_RATE, cls.ACCOST_INTER)
        return None, True

    @classmethod
    def get_spam_words(cls, region):
        lst = SpamWord.get_spam_words(region)
        if not lst:
            return 'not spam words', False
        return {'spam_words': lst}, True


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
        if not word:
            return False
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


DFAFilter.load()


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