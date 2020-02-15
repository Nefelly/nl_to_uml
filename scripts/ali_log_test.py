from litatom.service import ali_log_service
from time import time


def run():
    ali_log_service.AliLogService.get_histogram_by_time_and_topic()


if __name__ == "__main__":
    run()
