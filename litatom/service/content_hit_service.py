# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    HitTagWord
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
    def get_region_tag(cls, region, tag):
        return '%s_%s' % (region, tag)

    @classmethod
    def add(cls, keyword, tag, region=None, key_word_chains=None, default_key_word_chains=None):
        """以字典嵌套格式，将keyword的每个字母存入KEYWORD_CHAINS"""
        keyword = keyword.lower()
        chars = keyword.strip()
        if not chars:
            return
        if cls.NOT_REGION:
            level = default_key_word_chains[tag]
        else:
            region_tag = cls.get_region_tag(region, tag)
            if not key_word_chains.get(region_tag):
                key_word_chains[region_tag] = {}
            level = key_word_chains[region_tag]
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
        for tag in HitTagWord.get_tags():
            for region in GlobalizationService.REGIONS:
                for region_res in HitTagWord.get_by_region_tag(region, tag):
                    cls.add(region_res.word, tag, region, cls.KEYWORD_CHAINS, cls.DEFAULT_KEYWORD_CHAIN)


    @classmethod
    def get_hit_word(cls, word, tag, region=None):
        if not word:
            return False
        word = word.lower()
        ret = []
        start = 0
        while start < len(word):
            region_tag = cls.get_region_tag(region, tag)
            level = cls.KEYWORD_CHAINS.get(region_tag, {}) if not cls.NOT_REGION else cls.DEFAULT_KEYWORD_CHAIN.get(tag, {})
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
    def get_tag_words(cls, region, tag):
        lst = HitTagWord.get_tag_words(region.lower(), tag)
        if not lst:
            return 'not spam words', False
        return {'tag_words': lst}, True


ContentHitService.load()
