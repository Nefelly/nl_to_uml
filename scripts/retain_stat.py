import os
import sys
import fcntl
import datetime
from hendrix.conf import setting
from litatom.service import EmailService, RetainAnaService
import time
from litatom.util import (
    format_standard_date,
    ensure_path,
    get_zero_today,
    next_date,
    parse_standard_date,
)


def run(*date):
    """
    :param date: 默认参数代表前天留存，一个参数n则代表从前天前的n天到前天为止的留存，两个参数则具体化留存日期区间
    """
    if not date:
        from_date = next_date(get_zero_today(), -2)
        to_date = from_date
    elif len(date) < 2:
        to_date = next_date(get_zero_today(), -2)
        from_date = next_date(to_date, -int(date[0]))
    else:
        from_date = parse_standard_date(date[0])
        to_date = parse_standard_date(date[1])
    dst_addr = '/data/retain_ana/%s.xlsx' % (format_standard_date(from_date) + '-' + format_standard_date(to_date))
    ensure_path(dst_addr)
    RetainAnaService.get_retain_res(dst_addr, from_date, to_date)
    EmailService.send_file(["644513759@qq.com", "litatomwang@gmail.com", "w326571@126.com", '382365209@qq.com'], dst_addr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        run()
    elif len(sys.argv) < 3:
        run(sys.argv[1])
    else:
        run(sys.argv[1], sys.argv[2])
