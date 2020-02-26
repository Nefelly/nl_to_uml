from litatom.service import GoogleService, AliLogService
from datetime import *


def run():
    from_time = '2020-02-25 00:00:00+8:00'
    to_time = '2020-02-26 00:00:00+8:00'
    GoogleService.judge_history_pay_inform_log(from_time, to_time)


if __name__ == '__main__':
    run()
