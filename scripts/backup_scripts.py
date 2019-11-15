import os
import time
import sys
import langid

from litatom.mq import (
    MQProducer,
    MQConsumer
)
from litatom.model import *
from hendrix.conf import setting

def get_ages():
    m = {}
    for _ in User.objects():
        a = _.age
        if not m.has_key(a):
             m[a] = 1
        else:
            m[a] += 1
    print m


def stat_lang(objs):
     m = {}
     for o in objs:
         try:
             lan, score = langid.classify(o.nickname)
             if m.get(lan):
                 m[lan] += 1
             else:
                 m[lan] = 1
         except:
             continue
     return m

def stat_redis():
    t = ''
    m = {}
    cnt = 0
    tmp = 0
    k = open('/data/log/peak_monitor/peak_stat', 'r').read()
    for l in k.split('\n'):
             if '2019-11-14' in l:
                     if l != t:
                             cnt += 1
        
                     sc = True
                     t = l
             if 'total_commands_processed' in l:
                 if sc:
                         n = int(l.split(':')[1])
                 m[t] = n - tmp
                 tmp = n
                 sc = False

def cal_country_num():
    m = {}
    for _ in User.objects():
        c = _.country
        if not m.get(c):
            m[c] = 0
        m[c] += 1
    print m


if __name__ == "__main__":
    pass