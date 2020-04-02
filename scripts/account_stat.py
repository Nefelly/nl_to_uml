import sys
from litatom.service import AlertService, DiamStatService
import datetime
from litatom.util import ensure_path, get_zero_today


def run(stat_date=get_zero_today()):
    if stat_date:
        dst_addr = '/data/account_stat/%s.xlsx' % (stat_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        match_addr = '/data/match_account_stat/%s.xlsx' % (stat_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        dst_addr = '/data/account_stat/%s.xlsx' % (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
            '%Y-%m-%d')
        match_addr = '/data/match_account_stat/%s.xlsx' % (stat_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    ensure_path(dst_addr)
    ensure_path(match_addr)
    DiamStatService.diam_stat_report_7_days(dst_addr, stat_date)
    AlertService.send_file(["litatomwang@gmail.com","op.shiyang.yu@gmail.com","","w326571@126.com", '382365209@qq.com','644513759@qq.com'], dst_addr)
    DiamStatService.diam_free_report(match_addr,stat_date)
    AlertService.send_file(["litatomwang@gmail.com","op.shiyang.yu@gmail.com", "", "w326571@126.com", '382365209@qq.com','644513759@qq.com'], match_addr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        run()
    else:
        date_str = sys.argv[1]
        stat_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        run(stat_date)
