import os
import sys
import fcntl
from hendrix.conf import setting
from litatom.service import AlertService
import time

stat_len = 100
inter_val = 10
stat_queue = [(0, 0) for i in range(stat_len)]
alert_num = 4
stat_interval_s = 1
cnt = 0
alert_cnt = 0
lastest_alert_ts = 0

def monitor_error():
    err_file = '/data/log/litatom/err.json.log'
    y = os.popen('wc -l %s' % err_file).read().split(' ')[0]
    y = int(y)
    # stat_queue.append(int(y))
    ts = int(time.time())
    global cnt, lastest_alert_ts, alert_cnt
    cnt += 1
    stat_queue[cnt % 100] = (y, ts)
    last, last_ts = stat_queue[(cnt - inter_val) % 100]
    if last == 0:
        return
    err_line = y - last
    if err_line >= alert_num:
        judge_interval = 2 ** alert_cnt * 10
        if ts - lastest_alert_ts >= judge_interval:
            print "send alert!!!"
            if err_line < 20:
                res = os.popen('tail -n %d %s' % (err_line, err_file)).read()
                res_lst = [line for line in res.split("\n") if 'app(environ, start_response' not in line or "MainProcess" not in line or "NoneType" not in line]
                err_line = len(res_lst)
            if err_line >= alert_num:
                AlertService.send_mail(["382365209@qq.com"], "online, %d errors in %d secconds\n\n\n%s" % (err_line, ts - last_ts, '\n'.join(res_lst)))
            lastest_alert_ts = ts
            if alert_cnt >= 5 or (ts - lastest_alert_ts > 2 ** alert_cnt * 10 and lastest_alert_ts != 0):
                alert_cnt = 0

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
        monitor_error()
        time.sleep(stat_interval_s)

if __name__ == "__main__":
    run()

