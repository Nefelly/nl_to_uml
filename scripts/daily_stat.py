import os
import sys
import fcntl
import datetime
from hendrix.conf import setting
from litatom.service import AlertService, JournalService
import time
from litatom.util import (
    write_data_to_xls,
    ensure_path,
    now_date_key
)

def run():
    dst_addr = '/data/statres/%s.xlsx' % (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    dst_addr = '/data/statres/2019-11-28.xlsx'
    ensure_path(dst_addr)
    if not os.path.exists(dst_addr) or 1:
        JournalService.out_port_result(dst_addr)
    AlertService.send_file(["litatomwang@gmail.com", "w326571@126.com", '382365209@qq.com'], dst_addr)
    ad_addr = '/data/statres/%sad.xlsx' % (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    JournalService.ad_res(ad_addr)
    AlertService.send_file(["litatomwang@gmail.com", "w326571@126.com", '382365209@qq.com'], ad_addr)


if __name__ == "__main__":
    run()

