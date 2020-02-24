from litatom.service import AliLogService


def run():
    res_set = AliLogService.get_log_atom(project='litatomaction', logstore='litatomactionstore',
                                         query='action:match and remark:matchSuccess*|SELECT COUNT(1) as res GROUP BY user_id limit 1000000',
                                         from_time='2020-02-22 20:30:00+8:00',
                                         to_time='2020-02-23 20:30:00+8:00')
    print(res_set.get_count())
    for log in res_set.logs:
        log.get_time()


if __name__ == '__main__':
    run()
