import os
import sys
import fcntl
from hendrix.conf import setting
from litatom.service import (
    AlertService,
    UserService
)
from litatom.model import Feedback
import time

stat_len = 100
inter_val = 5 * 60
stat_queue = [(0, 0) for i in range(stat_len)]
alert_num = 3
stat_interval_s = 10
cnt = 0
alert_cnt = 0
lastest_alert_ts = 0

def inform_feedback():
    ts = int(time.time())
    judge_time = ts - inter_val
    global cnt, lastest_alert_ts, alert_cnt
    objs = Feedback.objects(passed=False, create_ts__gte=judge_time)
    if not objs:
        return
    res_lst = []
    for obj in objs:
        res_lst.append("\n".join(["user_id: " + obj.uid, "nickname:" + UserService.nickname_by_uid(obj.uid), "content:" + obj.content]))
        obj.passed = True
        obj.save()
    res = "\n-----------------------\n\n".join(res_lst)
    lastest_alert_ts = ts
    print "send feedback!!!"
    AlertService.send_mail(["382365209@qq.com"], res, "litatom feedback")


def run():
    mutex_f = '/var/run/%s.mutex' % __file__.split('/')[-1].replace('.py', '')
    if setting.IS_DEV:
        mutex_f += 'dev'
    f = open(mutex_f, 'w')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        print 'program already in run'
        sys.exit(0)
    while (True):
        inform_feedback()
        time.sleep(stat_interval_s)

if __name__ == "__main__":
    run()

