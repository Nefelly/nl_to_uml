from litatom.service import AliLogService
from . import add_api_to_alilog_condition
from datetime import *

file_set = ['/litatom/api/v1/__init__.py']
status_set = {200, 400, 404, 405, 408, 499, 500, 502, 503, 504}


def fetch_log(query):
    """
    根据输入的query，找出litatomstore近一分钟的日志
    :param query:
    :return:一个迭代器，迭代一个GetLogsResponse对象; 一个tuple描述起止时间
    """
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=-1)
    return AliLogService.get_log_by_time_and_topic(project='litatom', logstore='litatomstore', query=query,
                                                   from_time=AliLogService.datetime_to_alitime(start_time),
                                                   to_time=AliLogService.datetime_to_alitime(end_time)), (
               start_time, end_time)


def accum_stat(resp_set):
    """
    :param resp_set: 一个迭代器，迭代一个GetLogsResponse对象
    :return:平均响应时间，调用次数，错误返回频率，状态码计数
    """
    sum_resp_time = 0.0
    called_num = 0
    error_num = 0.0
    status_num = {}
    for status in status_set:
        status_num[status] = 0
    for resp in resp_set:
        resp.log_print()
        called_num += resp.get_count()
        for logs in resp.logs:
            contents = logs.get_contents()
            resp_time = contents['upstream_response_time']
            sum_resp_time += float(resp_time)
            status = int(contents['status'])
            if status in status_set:
                status_num[status] += 1
                if status >= 400:
                    error_num += 1

    return sum_resp_time / called_num, called_num, error_num / called_num, status_num


def put_stat_to_alilog(name, time, avg_resp_time, called_num, error_rate, status_num):
    contents = [('from_time', time[0]), ('to_time', time[1]), ('avg_response_time', avg_resp_time),
                ('called_num', called_num), ('error_rate', error_rate)]
    status_str = ''
    for status in status_num.keys():
        if status_num[status] > 0:
            status_str += status
            status_str += ':'
            status_str += status_num[status]
            status_str += ' '
    contents.append(('status_stat', status_str))
    AliLogService.put_logs(contents, project='litatommonitor', logstore='up-res-time-monitor', topic=name)


def run():
    query_list = add_api_to_alilog_condition.run(file_set)
    for query, name in query_list:
        resp_set, time = fetch_log(query)
        avg_resp_time, called_num, error_rate, status_num = accum_stat(resp_set)
        put_stat_to_alilog(name, time, avg_resp_time, called_num, error_rate, status_num)


if __name__ == '__main__':
    run()
