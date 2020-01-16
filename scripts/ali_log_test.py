import os
import sys
from litatom.service import AliLogService
from aliyun.log import *
import logging
import time
import datetime
from litatom.util import (
    write_data_to_xls,
    ensure_path,
    now_date_key
)


def run():
    contents = [('e', '5'), ('f', '6')]
    AliLogService.put_logs(contents)


if __name__ == "__main__":
    run()
