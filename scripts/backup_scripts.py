import os
import time
import sys
import datetime
import langid

from litatom.mq import (
    MQProducer,
    MQConsumer
)
from litatom.model import (
    UserSetting,
    User,
    Uuids,
    MatchRecord
)
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

def stat_avr_time():
    mm = {}
    for _ in MatchRecord.objects(quit_user__ne=None):
             u1 = _.user_id1
             u2 = _.user_id2
             if not mm.get(u1):
                mm[u1] = [_.inter_time]
             else:
                mm[u1].append(_.inter_time)
             if not mm.get(u2):
                mm[u2] = [_.inter_time]
             else:
                mm[u2].append(_.inter_time)
        

def stat_register_rate():
    ls = UserSetting.objects(create_time__gte=datetime.datetime(2019, 11, 18),
                             create_time__lte=datetime.datetime(2019, 11, 19)).distinct('uuid')
    ts = Uuids.objects(create_time__gte=datetime.datetime(2019, 11, 18),
                       create_time__lte=datetime.datetime(2019, 11, 19)).distinct('uuid')
    m = {}
    cnt = 0
    for l in ls:
        if l in m:
            cnt += 1
    uids = [UserSetting.get_by_user_id(str(el.id)) for el in
            User.objects(create_time__gte=datetime.datetime(2019, 11, 18), create_time__lte=datetime.datetime(2019, 11, 19))]
    ms = [el.uuid for el in uids]
    mm = []
    for l in ms:
        if l not in m:
            mm.append(l)
    kk = [UserSetting.objects(uuid=el).count() for el in mm]

if __name__ == "__main__":
    pass