# coding: utf-8
import json
import time
import traceback
import logging
import mmh3
import random
from flask import (
    request
)
from hendrix.conf import setting
from ..key import (
    REDIS_EXP,

)
from ..const import (
    ONE_DAY,

)
from ..model import (
    ExpBucket
)

from ..redis import RedisClient

logger = logging.getLogger(__name__)

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']
volatile_redis = RedisClient()['volatile']

class ExperimentService(object):
    '''
    参考文档： 美团实验平台设计  https://tech.meituan.com/2019/11/28/advertising-performance-experiment-configuration-platform.html
              马蜂窝  https://blog.csdn.net/weixin_43846997/article/details/90512001
    '''
    BUCKET_NUM = 100

    USER_EXP_TTL = ONE_DAY
    WHITE_LIST_TTL = 30 * ONE_DAY

    @classmethod
    def get_conf(cls):
        exp_key = 'exp_name'
        paths_key = 'paths'
        res = {
            "experiments": [
                {
                    paths_key:[
                        "anoy_match/get_fakeid",
                        "anoy_match/anoy_match"
                    ],
                    exp_key: "match_strategy"
                },
                {
                    paths_key: ["user/accost"],
                    exp_key: "accost"
                },
                {
                    paths_key: ["anoy_match/times_left"],
                    exp_key:  "times_left_exp"
                }
            ]
        }
        return res

    @classmethod
    def _get_key(cls, key, exp_name):
        key_exp = '%s_%s' % (key, exp_name)
        return REDIS_EXP.format(key_exp=key_exp)

    @classmethod
    def set_exp(cls, key=None, expire=7 * ONE_DAY):
        if not key:
            key = request.user_id
        if key is None:
            return True
        exp_name = request.experiment_name
        if not exp_name:
            return
        exp_value = request.experiment_value
        if exp_value == 'reset':
            '''测试环境可以重新设置值'''
            if setting.IS_DEV:
                redis_client.delete(cls._get_key(key, exp_name))
            return
        if exp_value is None:
            return
        redis_client.set(cls._get_key(key, exp_name), exp_value, ex=expire)
        return True

    @classmethod
    def get_exp_value(cls, exp_name, key=None):
        if not key:
            key = request.user_id
        return redis_client.get(cls._get_key(key, exp_name))

    @classmethod
    def _get_bucket(cls, exp_name, key=None):
        if not key:
            key = request.user_id
        return mmh3.hash(key + exp_name) % cls.BUCKET_NUM

    @classmethod
    def lit_exp_value(cls, exp_name, key=None):
        '''
        :param exp_name:
        :param key:
        :return: 该实验命中的规则
        impl： hash  得到桶后
        '''
        if not key:
            key = request.user_id
        bucket = cls._get_bucket(exp_name, key)
        return ExpBucket.get_by_exp_name_bucket_id(exp_name, bucket)

    @classmethod
    def adjust_buckets(cls, exp_name, value_bucket_num_dict):
        '''
        :param exp_name:
        :param value_bucket_num_dict: {'delay': 15, 'default': 12, 'acc': 82}  除default外 合起来要小于 cls.BUCKET_NUM
        :return: 如果是合理的 就为结果的各个value 及里面包含的桶  {'delay': [1,5,8, 12...], 'default': [6, 7, 10]}如果不合理 就返回错误
        '''
        # 判断传值是否准确
        total = sum([value_bucket_num_dict.get(e) for e in value_bucket_num_dict if e != ExpBucket.NOSET])
        if total > cls.BUCKET_NUM:
            return u'wrong arguments, total bucket num exceed max:%d' % cls.BUCKET_NUM, False

        # 先加载
        old_buckets, status = cls.get_buckets(exp_name)

        # 计算需要更换的，最小准则
        need_adjust = {}
        for value in value_bucket_num_dict:
            if value in [ExpBucket.NOSET]:
                continue
            new_num = value_bucket_num_dict[value]
            old_num = len(old_buckets.get(value, []))
            need_adjust[value] = new_num - old_num
        # release_num = -sum([el for el in need_adjust.values() if el < 0])
        add_num = sum([el for el in need_adjust.values() if el > 0])
        old_noset = []
        old_noset = old_buckets[ExpBucket.NOSET]
        old_noset_num = len(old_noset)

        def add_new(value, num, old_noset):
            buckets = sys_rnd.sample(old_noset, num)
            for b in buckets:
                print 'creating', exp_name, b, value
                ExpBucket.create(exp_name, b, value)
            old_noset = [el for el in old_noset if el not in buckets]
            return old_noset

        def release_old(value, num, old_noset):
            num = - num if num < 0 else num
            buckets = sys_rnd.sample(old_buckets[value], num)
            for b in buckets:
                ExpBucket.create(exp_name, b, ExpBucket.NOSET)
            old_noset += buckets
            old_buckets[value] = [el for el in old_buckets[value] if el not in buckets]
            return old_noset

        def release_all_old(old_noset):
            for value in need_adjust:
                if need_adjust[value] < 0:
                    old_noset = release_old(value, need_adjust[value], old_noset)
            return old_noset

        def add_all_new(old_noset):
            for value in need_adjust:
                if need_adjust[value] > 0:
                    old_noset = add_new(value, need_adjust[value], old_noset)
            return old_noset

        if old_noset_num > add_num:
            ''' 格子够  先从未实验的取 以减少以前的影响'''
            old_noset = add_all_new(old_noset)
            old_noset = release_all_old(old_noset)
        else:
            '''格子不够 得先释放 再取'''
            old_noset = release_all_old(old_noset)
            old_noset = add_all_new(old_noset)
        return cls.get_buckets(exp_name)

    @classmethod
    def get_buckets(cls, exp_name):
        buckets = ExpBucket.load_buckets(exp_name)
        used_bucket = {}
        for i in range(cls.BUCKET_NUM):
            used_bucket[i] = False

        for el in buckets:
            for _ in buckets[el]:
                used_bucket[_] = True

        if not buckets.get(ExpBucket.NOSET):
            buckets[ExpBucket.NOSET] = []
        buckets[ExpBucket.NOSET] += [el for el in used_bucket if not used_bucket[el]]
        for el in buckets:
            buckets[el] = sorted(buckets[el])
        return buckets, True

    @classmethod
    def load_bucket_value_m(cls, exp_name):
        buckets, status = cls.get_buckets(exp_name)
        res = {}
        for value in buckets:
            for bucket in buckets[value]:
                res[bucket] = value
        return res

    @classmethod
    def get_all_experiments(cls):
        exp_names = ExpBucket.objects().distinct('exp_name')
        total_num = len(exp_names)
        res = {
            'total_num': total_num,
            'exp_names': exp_names
        }
        return res, True

    @classmethod
    def test_get_all_bucket(cls, exp_name):
        s = time.time()
        keys = volatile_redis.smembers('all_se')
        m = time.time()
        print 'getting keys using:', m - s # 200w 12s 16w qps
        res = {}
        for _ in keys:
            bucket = cls._get_bucket(exp_name, _)
            if res.get(bucket):
                res[bucket].add(_)
            else:
                res[bucket] = set([_])
        print 'get bucket using:', time.time() - m # 200w 3s 60w qps
        return res

    @classmethod
    def testing_orthogonal(cls):
        '''
        检测分桶是否正常
        :return:
        '''
        test15 = cls.test_get_all_bucket('test15')
        test16 = ExperimentService.test_get_all_bucket('test16')

        print '检测分布均匀： test15 各个桶大小'
        for _ in test15:
            print _, len(test15[_])

        print '检测桶分配没有重合， test15[0] & test15[1]'
        test15[0] & test15[1]

        print '检测不同实验之间正交'
        print 'len(test16[0] & test15[1])'
        len(test16[0] & test15[1])

        print 'len(test16[0] & test15[2])'
        len(test16[0] & test15[2])

        print 'len(test16[1] & test15[1])'
        len(test16[1] & test15[1])

    @classmethod
    def set_or_disable_white_list(cls, exp_name):
        '''
        设置白名单
        :param exp_name:
        :return:
        '''
        pass

    @classmethod
    def batch_get_id_values(cls, exp_name, ids):
        '''
        批量获取用户对应实验的value
        :param exp_name:
        :param ids:
        :return:
        '''
        id_values = {}
        pass

    @classmethod
    def get_exp_bucket_values(cls, exp_name):
        pass

    @classmethod
    def remove_bucket(cls, exp_name, bucket_number):
        pass

    @classmethod
    def add_bucket(cls):
        pass

    @classmethod
    def get_user_experiment_from_logs(cls, query, from_time, to_time):
        from ..model import User
        # User.get_user_id_by_session(sid)
        pass
