from litatom.service import AliLogService
from . import add_api_to_alilog_condition
from datetime import *

file_set = ['/litatom/api/v1/__init__.py']
status_set = {200, 400, 404, 405, 408, 499, 500, 502, 503, 504}


def fetch_log(query):
    """
    根据输入的query，找出litatomstore近一分钟的日志
    :param query:
    :return:一个迭代器，迭代一个GetLogsResponse对象
    """
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=-1)
    return AliLogService.get_log_by_time_and_topic(project='litatom', logstore='litatomstore', query=query,
                                                   from_time=AliLogService.datetime_to_alitime(start_time),
                                                   to_time=AliLogService.datetime_to_alitime(end_time))


def accum_stat(resp_set):
    """

    :param resp_set: 一个迭代器，迭代一个GetLogsResponse对象
    :return:
    """
    sum_resp_time = 0.0
    called_num = 0
    status_num = {}
    for status in status_set:
        status_num[status] = 0
    for resp in resp_set:
        for logs in resp.logs:
            called_num +=
            contents = logs.get_contents()


def run():
    query_list = add_api_to_alilog_condition.run(file_set)
    for query, name in query_list:
        resp_set = fetch_log(query)
        sum_resp_time = 0.0
        called_num = 0
        status_num = {}
        for resp in resp_set:
            called_num += resp.get_logs()
            for logs in resp.logs:
                contents = logs.get_contents()
                resp_time = contents['upstream_response_time']
                sum_resp_time += resp_time



if __name__ == '__main__':
    run()
