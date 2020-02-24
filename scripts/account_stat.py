import os
import sys
import fcntl
import datetime
from hendrix.conf import setting
from litatom.service import AlertService, JournalService, AliLogService, DiamStatService
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
        dst_addr = '/data/account_stat/%s.xlsx' % (stat_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        match_addr = '/data/match_account_stat/%s/xlsx' % (stat_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        dst_addr = '/data/account_stat/%s.xlsx' % (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
            '%Y-%m-%d')
        match_addr = '/data/match_account_stat/%s/xlsx' % (stat_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    ensure_path(dst_addr)
    DiamStatService.diam_stat_report(dst_addr, stat_date)
    AlertService.send_file(['644513759@qq.com'], dst_addr)
    DiamStatService.diam_free_report(match_addr,stat_date)
    AlertService.send_file(['644513759@qq.com'], match_addr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        run()
    else:
        date_str = sys.argv[1]
        stat_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        run(stat_date)
