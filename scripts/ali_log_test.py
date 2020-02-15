from litatom.service import ali_log_service
from time import time


def run():
    ali_log_service.AliLogService.get_log_by_time(project='litatom', logstore='litatomstore', size=100,
                                                  query='body_bytes_sent:90',
                                                  attributes=['request_uri', 'time', 'body_bytes_sent'])


if __name__ == "__main__":
    run()
