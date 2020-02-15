from litatom.service import ali_log_service
from time import time


def run():
    print("debug1")
    ali_log_service.AliLogService.get_log_by_time_and_topic(from_time=int(time()-500),to_time=int(time()))
    print("debug2")
    ali_log_service.AliLogService.get_log_by_time(from_time=int(time()-500),to_time=int(time()))


if __name__ == "__main__":
    run()
