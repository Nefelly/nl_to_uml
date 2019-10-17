import os
from litatom.service import AlertService
import time

stat_len = 100
inter_val = 20
stat_queue = [(0, 0) for i in range(stat_len)]
alert_num = 1
stat_interval_s = 1
cnt = 0

def monitor_error():
    y = os.popen('wc -l /data/log/litatom/err.json.log').read().split(' ')[0]
    # stat_queue.append(int(y))
    ts = int(time.time())
    global cnt
    cnt += 1
    stat_queue[cnt % 100] = (y, ts)
    last, last_ts = stat_queue[(cnt - inter_val) % 100]
    if last == 0:
        return
    if y - last >= alert_num:
        AlertService.send_mail(["382365209@qq.com"], "online, %d errors in %d secconds" % (y - last, ts - last_ts))
        print "send alert!!!"

if __name__ == "__main__":
    while(True):
        monitor_error()
        time.sleep(0.2)

