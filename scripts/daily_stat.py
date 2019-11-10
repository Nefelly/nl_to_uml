import os
import sys
import fcntl
from hendrix.conf import setting
from litatom.service import AlertService, JournalService
import time
from litatom.util import (
    write_data_to_xls,
    ensure_path,
    now_date_key
)

def run():
    dst_addr = '/data/statres/%s.xlsx' % now_date_key()
    ensure_path(dst_addr)
    if not os.path.exists(dst_addr):
        JournalService.out_port_result(dst_addr)
    AlertService.send_file('382365209@qq.com', dst_addr)


if __name__ == "__main__":
    run()

