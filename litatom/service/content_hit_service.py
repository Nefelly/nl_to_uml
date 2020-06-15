# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    FeedTagWord
)
from ..service import (
    GlobalizationService
)
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class ContentHitService(object):
    KEYWORD_CHAINS = {}
    DEFAULT_KEYWORD_CHAIN = {}
    DELIMIT = '\x00'
    NOT_REGION = False

    @classmethod
    def add(cls, keyword, tag, region=None, key_word_chains=None, default_key_word_chains=None):
        """以字典嵌套格式，将keyword的每个字母存入KEYWORD_CHAINS"""
        keyword = keyword.lower()
        chars = keyword.strip()
        if not chars:
            return
        if cls.NOT_REGION:
            level = default_key_word_chains
        else:
            if not key_word_chains.get(region):
                key_word_chains[region] = {}
            level = key_word_chains[region]
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
        for tag in FeedTagWord.get_tags():
            for region in GlobalizationService.REGIONS:
                for region_res in FeedTagWord.get_by_region_tag(region, tag):
                    cls.add(region_res.word, region, cls.KEYWORD_CHAINS, cls.DEFAULT_KEYWORD_CHAIN)


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
        if not word:
            return False
        if not region and online:
            region = GlobalizationService.get_region()
        if cls.NOT_REGION:
            if cls.hit_word_in_chains(word, cls.DEFAULT_KEYWORD_CHAIN):
                return not cls.hit_word_in_chains(word, cls.DEFAULT_FAKE_KEYWORD_CHAIN)
            else:
                return False
        else:
            if cls.hit_word_in_chains(word, cls.KEYWORD_CHAINS, region):
                return not cls.hit_word_in_chains(word, cls.FAKE_KEYWORD_CHAINS,region)
            else:
                return False

    @classmethod
    def hit_word_in_chains(cls, word, key_word_chain, tag, region=None):
        """从word的某个位置开始连续匹配到了一个keyword，则判定为spam_word"""
        word = word.lower()
        ret = []
        start = 0
        while start < len(word):
            if not region:
                level = key_word_chain
            else:
                level = key_word_chain.get(region, {})
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
        lst = FeedTagWord.get_spam_words(region.lower())
        if not lst:
            return 'not spam words', False
        return {'spam_words': lst}, True


ContentHitService.load()
