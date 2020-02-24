from litatom.service import AliLogService


def run():
    resp = AliLogService.get_log_by_time_and_topic(from_time='2020-02-23 19:12:00+8:00',to_time='2020-02-24 19:12:00+8:00',size=100000,
                              query='name:deposit and diamonds:100|SELECT COUNT(DISTINCT user_id) as res',project='litatom-account',
                                                   logstore='account_flow')

    for i in resp:
        i.log_print()

if __name__ == '__main__':
    run()
