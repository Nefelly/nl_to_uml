import datetime
from litatom.service import (
    MonitorService
)
from litatom.util import (
    format_standard_time
)


def run(start_time=datetime.datetime.now() + datetime.timedelta(minutes=-5),
        end_time=datetime.datetime.now()):
    dst_addr = "api_monitor"
    MonitorService.output_report(dst_addr, start_time, end_time)


if __name__ == '__main__':
    run()
