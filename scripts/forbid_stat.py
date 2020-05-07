import sys
import os
import datetime
from litatom.service import (
    ForbidStatService,
    EmailService
)
from litatom.util import (
    ensure_path,
    parse_standard_date,
    now_date_key,
    parse_standard_time,
    date_to_int_time,
    format_standard_time,
)


def run(from_time=parse_standard_date(now_date_key()), to_time=datetime.datetime.now()):
    dst_addr = '/data/tmp/forbid_history:%s.json' % (format_standard_time(from_time)+'-'+format_standard_time(to_time))
    ForbidStatService.get_forbid_history(dst_addr, date_to_int_time(from_time), date_to_int_time(to_time))
    EmailService.send_file(["litatomwang@gmail.com", "op.shiyang.yu@gmail.com", "396408395@qq.com", "w326571@126.com", '382365209@qq.com', '644513759@qq.com'], dst_addr)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        run()
    else:
        run(parse_standard_time(sys.argv[1]), parse_standard_time(sys.argv[2]))
