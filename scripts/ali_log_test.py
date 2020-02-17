from litatom.service import AliLogService


def run():
    res = AliLogService.get_log_by_time(query='action:match | SELECT DISTINCT user_id,location LIMIT 10000')
    res.log_print()


if __name__ == '__main__':
    run()
