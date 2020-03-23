# encoding:utf-8
from litatom.service import AliLogService

def run():
    resp_set = AliLogService.get_log_by_time_and_topic(from_time='2020-03-20 00:00:00+8:00',
                                                       to_time='2020-03-21 00:00:00+8:00',
                                                       query = '*|select distinct user_id limit 1000000')
    cnt=0
    uids=set()
    for resp in resp_set:
        cnt+=resp.get_count()
        if cnt%2000 == 0:
            print(cnt)
        for log in resp.logs:
            uids.add(log.get_contents()['user_id'])


    print(cnt)


if __name__ == '__main__':
    run()