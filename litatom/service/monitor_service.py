# coding: utf-8
import re
import os
from litatom.util import str2float
from datetime import *
from ..service import AliLogService


class MonitorService(object):
    FILE_SET = ['/litatom/api/v1/__init__.py']
    STATUS_SET = {200, 400, 404, 405, 408, 499, 500, 502, 503, 504}
    QUERY_ANALYSIS = '|SELECT avg(upstream_response_time) as avg_response_time,' \
                     'count(1) as called_num,avg(status) as avg_status'

    @classmethod
    def get_query_is(cls, file_path):
        """
        :param file_path: 一个带有api接口的文件路径
        :return: 返回一个tuple的列表 [(query_condition, condition_name),...]
        query_condition是阿里云日志服务相应的查询条件，即query字符串，condition_name是该str变量名字，按照接口路径和请求方式命名：
        eg. ('request_uri:/api/sns/v1/lit/user/avatars AND request_method:GET', ALILOG_USER_AVATARS)
            ('request_uri:/api/sns/v1/lit/user/info AND request_method:POST',ALILOG_USER_INFO_P)
        """
        res = []
        with open(file_path) as f:
            lines = f.readlines()
            valid_head_pattern = 'b.add_url_rule\(\'/lit/'
            valid_body_pattern = '[a-z0-9_]+[/\']'
            uri_pattern = "'[^']+'"
            post_pattern = 'POST'
            name_head = 'ALILOG'
            condition_head = 'request_uri:/api/sns/v1/lit'
            condition_tail_get = ' AND request_method:GET'
            condition_tail_post = ' AND request_method:POST'
            for line in lines:
                if not line or not line.strip():
                    continue
                if line.strip()[0] == '#':
                    continue
                head = re.match(valid_head_pattern, line)
                if head:
                    end_head_pos = head.span()[1]
                    uri = re.search(uri_pattern, line)
                    if uri:
                        uri = uri.span()
                        uri = line[uri[0]:uri[1]]

                    post_tag = False
                    if re.search(post_pattern, line):
                        post_tag = True
                    line = line[end_head_pos:]
                    body = []
                    while True:
                        body_part = re.match(valid_body_pattern, line)
                        if not body_part:
                            break
                        end_part_pos = body_part.span()[1]
                        body.append(line[:end_part_pos - 1])
                        line = line[end_part_pos:]
                    name = name_head
                    condition = condition_head
                    for part in body:
                        name += '_'
                        condition += '/'
                        condition += part
                        name += part.upper()
                    if post_tag:
                        name += '_P'
                        condition += condition_tail_post
                    else:
                        condition += condition_tail_get
                    res_tuple = (condition, name, uri, post_tag)
                    res.append(res_tuple)

        return res

    @classmethod
    def get_query_from_files(cls, path_set):
        """
        :param path_set: 一个文件名的列表，文件中包含api接口描述，eg.['/litatom/api/v1/__init__.py',...]
        :return: 返回值同get_query_is，实际上将其结果整合
        """
        res = []
        for path in path_set:
            file_path = os.getcwd() + path
            res += cls.get_query_is(file_path)
        return res

    @classmethod
    def fetch_log(cls, query):
        """
        根据输入的query，找出litatomstore近一分钟的日志
        :param query:
        :return:一个迭代器，迭代一个GetLogsResponse对象; 一个tuple描述起止时间
        """
        end_time = datetime.now()
        start_time = end_time + timedelta(minutes=-1)
        return AliLogService.get_log_by_time_and_topic(project='litatom', logstore='litatomstore', query=query,
                                                       from_time=AliLogService.datetime_to_alitime(start_time),
                                                       to_time=AliLogService.datetime_to_alitime(end_time)), (
                   start_time, end_time)

    @classmethod
    def accum_stat(cls, resp_set):
        """
        :param resp_set: 一个迭代器，迭代一个GetLogsResponse对象
        :return:平均响应时间，调用次数，错误返回频率，状态码计数
        """
        sum_resp_time = 0.0
        called_num = 0
        error_num = 0.0
        status_num = {}
        for status in cls.STATUS_SET:
            status_num[status] = 0
        for resp in resp_set:
            called_num += resp.get_count()
            for logs in resp.logs:
                contents = logs.get_contents()
                resp_time = contents['upstream_response_time']
                resp_time = str2float(resp_time)
                if resp_time:
                    sum_resp_time += resp_time
                status = int(contents['status'])
                if status in cls.STATUS_SET:
                    status_num[status] += 1
                    if status >= 400:
                        error_num += 1
        if called_num > 0:
            return sum_resp_time / called_num, called_num, error_num / called_num, status_num
        else:
            return 0, 0, 0, None

    @classmethod
    def put_stat_to_alilog(cls, name, time, avg_resp_time, called_num, error_rate, status_num, uri, is_post):
        contents = [('from_time', AliLogService.datetime_to_alitime(time[0])), ('request_uri', uri),
                    ('to_time', AliLogService.datetime_to_alitime(time[1])), ('error_rate', str(error_rate)),
                    ('avg_response_time', str(avg_resp_time)), ('called_num', str(called_num))]
        if is_post:
            contents.append(('request_method', 'POST'))
        else:
            contents.append(('request_method', 'GET'))
        if status_num:
            status_str = ''
            for status in status_num.keys():
                if status_num[status] > 0:
                    status_str += str(status)
                    status_str += ':'
                    status_str += str(status_num[status])
                    status_str += ' '
            contents.append(('status_stat', status_str))
        AliLogService.put_logs(contents, project='litatommonitor', logstore='up-res-time-monitor', topic=name)

    # @classmethod
    # def read_stat

    @classmethod
    def monitor_report(cls):
        query_list = cls.get_query_from_files(cls.FILE_SET)
        for query, name, uri, is_post in query_list:
            resp_set, time = cls.fetch_log(query+cls.QUERY_ANALYSIS)
            avg_resp_time, called_num, error_rate, status_num = cls.accum_stat(resp_set)
            cls.put_stat_to_alilog(name, time, avg_resp_time, called_num, error_rate, status_num, uri, is_post)

