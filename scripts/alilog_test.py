# encoding:utf-8
from litatom.service import AliLogService


def run():
    resp_set = AliLogService.get_log_by_time_and_topic(from_time='2020-03-16 00:00:00+8:00',
                                                       to_time='2020-03-17 00:00:00+8:00',
                                                       query='*| select distinct user_id limit 1000000')
    for resp in resp_set:
        for log in resp.logs:
            log.log_print()


if __name__ == '__main__':
    run()
