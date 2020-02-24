from litatom.service import DiamStatService


def run():
    resp = DiamStatService.fetch_log(from_time='2020-02-23 19:12:00+8:00',to_time='2020-02-24 19:12:00+8:00',
                              query='name:deposit and diamonds=100|SELECT COUNT(DISTINCT user_id) as res)')

    resp.log_print()

if __name__ == '__main__':
    run()
