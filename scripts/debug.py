from litatom.service import AliLogService


def run():
    resp_set=AliLogService.get_log_atom(from_time='2020-03-31 00:00:00+8:00',
                                        to_time='2020-04-01 00:00:00+8:00',
                                        project='litatom-account',logstore='account_flow',
                                        query='name:unban_by_diamonds | SELECT -sum(diamonds) as res')
    resp_set.log_print()

if __name__=='__main__':
    run()