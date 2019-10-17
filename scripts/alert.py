import os
from litatom.service import AlertService
import time

stat_len = 100
inter_val = 20
stat_queue = [0 for i in range(stat_len)]
alert_num = 15
stat_interval_s = 1

def monitor_error():
    y = os.popen('wc -l /data/log/litatom/err.json.log').read().split(' ')[0]
    # stat_queue.append(int(y))
    ts = int(time.time())
    stat_queue[ts % 100] = y
    last = stat_queue[(ts - inter_val)]
    if last == 0:
        return
    if y - last >= alert_num:
        AlertService.send_mail(["382365209@qq.com"], "error online")

if __name__ == "__main__":
    while(True):
        monitor_error()
        time.sleep(0.2)

