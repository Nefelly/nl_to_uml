from litatom.service import AliLogService


def run():
    res_set = AliLogService.get_log_atom(project='litatom-account', logstore='account_flow',
                                         query='name:deposit and diamonds=50|SELECT COUNT(DISTINCT user_id) as res',
                                         from_time='2020-02-22 20:30:00+8:00',
                                         to_time='2020-02-23 20:30:00+8:00')
    print(res_set.get_count())
    for log in res_set.logs:
        log.log_print()


if __name__ == '__main__':
    run()
