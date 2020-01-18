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


def run():
    contents = [('test', 0)]
    AliLogService.put_logs(contents, project="litatommonitor", logstore="daily-stat-monitor")


if __name__ == "__main__":
    run()
