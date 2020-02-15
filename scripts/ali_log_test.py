from litatom.service import ali_log_service


def run():
    ali_log_service.AliLogService.get_log_by_time_and_topic()


if __name__ == "__main__":
    run()
