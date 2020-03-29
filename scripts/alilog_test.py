from litatom.service import AliLogService


def run():
    res = AliLogService.get_log_atom(from_time='2020-03-29 00:00:00+8:00', to_time='2020-03-29 18:00:00+8:00',
                                     query='remark:share\ prepare | select count(*) as res')

    res.log_print()


if __name__ == '__main__':
    run()
