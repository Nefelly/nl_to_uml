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