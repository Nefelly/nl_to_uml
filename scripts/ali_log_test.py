from litatom.service import AliLogService


def run():
    res = AliLogService.get_log_by_time_and_topic(from_time='2020-02-16 00:00:00+8:00', to_time='2020-02-16 23:59:59+8:00',
                                                  size=400000)


if __name__ == '__main__':
    run()
