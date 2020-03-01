from litatom.service import AliLogService

def run():
    resp = AliLogService.get_log_atom(from_time='2020-03-01 00:00:00+8:00', to_time='2020-03-01 3:00:00+8:00',
                                                       query='*|select distinct user_id,location', size=-1)
    num = 0
    print(resp.get_count())


if __name__ == '__main__':
    run()