import os
import sys
from litatom.service import AliLogService
import time
import datetime
from litatom.util import (
    write_data_to_xls,
    ensure_path,
    now_date_key
)


def run():
    contents = [('a', 'b')]
    print 'contents',contents
    res = AliLogService.put_logs(contents)
    print res


if __name__ == "__main__":
    run()
