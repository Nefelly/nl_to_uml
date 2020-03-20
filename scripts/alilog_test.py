# encoding:utf-8
from litatom.service import AliLogService
from litatom.model import User
from litatom.util import *


def run():
    resp_set = AliLogService.get_log_by_time_and_topic(from_time='2020-03-15 00:00:00+8:00',
                                                       to_time='2020-03-16 00:00:00+8:00',
                                                       query='*| select distinct user_id limit 5000000')
    uids=set()
    for resp in resp_set:
        for log in resp.logs:
            contents = log.get_contents()
            uids.add(contents['user_id'])
    print(len(uids))

if __name__ == '__main__':
    run()
