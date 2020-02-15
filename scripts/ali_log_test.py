from litatom.service import ali_log_service
from time import time


def run():
    ali_log_service.AliLogService.get_log_by_time(project='litatom', logstore='litatomstore',size=100,
                                                  attributes=['request_uri', 'time', 'upstream_response_time'])


if __name__ == "__main__":
    run()
