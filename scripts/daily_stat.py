import os
import sys
from litatom.service import AlertService, JournalService
import datetime
from litatom.util import (
    ensure_path,
)
from litatom.model import (
    StatItems
)


def run(stat_date=None):
    # stat_date = datetime.datetime(2019, 11, 27)
    def real():
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
        print(dst_addr)
        if not os.path.exists(dst_addr) or 1:
            JournalService.out_port_result(dst_addr, stat_date, StatItems.BUSINESS_TYPE)
        AlertService.send_file(["litatomwang@gmail.com", "op.shiyang.yu@gmail.com","396408395@qq.com","w326571@126.com", '382365209@qq.com','644513759@qq.com'],dst_addr)
        JournalService.out_port_result(ad_addr, stat_date, StatItems.AD_TYPE)
        AlertService.send_file(["litatomwang@gmail.com", "op.shiyang.yu@gmail.com","396408395@qq.com","w326571@126.com", '382365209@qq.com','644513759@qq.com'],ad_addr)
    for i in range(5):
        try:
            real()
            break
        except Exception, e:
            print e
            continue


if __name__ == "__main__":
    if len(sys.argv) < 2:
        run()
    else:
        date_str = sys.argv[1]
        stat_date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d')
        print(stat_date)
        run(stat_date)
