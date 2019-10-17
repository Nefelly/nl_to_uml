import os
from litatom.service import AlertService
import time

stat_len = 100
inter_val = 20
stat_queue = [(0, 0) for i in range(stat_len)]
alert_num = 1
stat_interval_s = 1
cnt = 0
alert_cnt = 0
lastest_alert_ts = 0

def monitor_error():
    y = os.popen('wc -l /data/log/litatom/err.json.log').read().split(' ')[0]
    y = int(y)
    # stat_queue.append(int(y))
    ts = int(time.time())
    # global cnt
    cnt += 1
    stat_queue[cnt % 100] = (y, ts)
    last, last_ts = stat_queue[(cnt - inter_val) % 100]
    if last == 0:
        return
    # global  lastest_alert_ts
    if y - last >= alert_num:
        judge_interval = 2 ** alert_cnt * 10
        if ts - lastest_alert_ts >= judge_interval:
            AlertService.send_mail(["382365209@qq.com"], "online, %d errors in %d secconds" % (y - last, ts - last_ts))
            lastest_alert_ts = ts
            if alert_cnt >= 5:
                alert_cnt = 0
        print "send alert!!!"

if __name__ == "__main__":
    while(True):
        monitor_error()
        time.sleep(0.2)

