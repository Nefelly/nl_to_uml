import os
import sys
import fcntl
import datetime
from hendrix.conf import setting
from litatom.service import AlertService, JournalService, AliLogService
import time
import datetime
from litatom.util import (
    write_data_to_xls,
    ensure_path,
    now_date_key
)

def run(stat_date=None):
    # stat_date = datetime.datetime(2019, 11, 27)
    if stat_date:
        JournalService.ZERO_TODAY = stat_date
        dst_addr = '/data/statres/%s.xlsx' % (stat_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        ad_addr = '/data/statres/%sad.xlsx' % (stat_date - datetime.timedelta(days=1)).strftime(
            '%Y-%m-%d')
    else:
        dst_addr = '/data/statres/%s.xlsx' % (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        ad_addr = '/data/statres/%sad.xlsx' % (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
            '%Y-%m-%d')
    ensure_path(dst_addr)
    if not os.path.exists(dst_addr) or 1:
        JournalService.out_port_result(dst_addr,stat_date)
    # AlertService.send_file(["litatomwang@gmail.com", "w326571@126.com", '382365209@qq.com'], dst_addr)
    AlertService.send_file(['644513759@qq.com'], dst_addr)
    JournalService.ad_res(ad_addr,stat_date)
    # AlertService.send_file(["litatomwang@gmail.com", "w326571@126.com", '382365209@qq.com'], ad_addr)
    AlertService.send_file(['644513759@qq.com'], ad_addr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        run()
    else:
        date_str = sys.argv[1]
        stat_date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        print stat_date
        run(stat_date)
