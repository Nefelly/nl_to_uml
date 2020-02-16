from litatom.service import AliLogService
from time import time


def run():
    start_match_logs = AliLogService.get_log_by_time(query='remark:startMatch and action:match',size=100,
                                                     from_time="2020-02-15 00:00:00+8:00",
                                                     to_time="2020-02-15 00:22:00+8:00")
    start_match_logs.log_print()
    # for start_match_log in start_match_logs.logs:
    #     contents = start_match_log.get_contents()
    #     time = start_match_log.get_time()
    #     match_success_text_logs = AliLogService.get_log_by_time_and_topic(from_time=time, to_time=time + 180, query='remark:matchSuccesstext and action:match')


if __name__ == "__main__":
    run()
