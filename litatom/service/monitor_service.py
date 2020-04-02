# coding: utf-8
import re
import os
from ..util import (
    write_data_to_xls,
    parse_standard_time
)
from datetime import *
from ..service import (
    AliLogService,
    AlertService,
)


class MonitorService(object):
    FILE_SET = ['/litatom/api/v1/__init__.py']
    STATUS_SET = {200, 400, 404, 405, 408, 499, 500, 502, 503, 504}
    STAT_ANALYSIS = {
        'called_num': '| SELECT count(1) as res',
        'avg_status': '| SELECT avg(status) as res',
        'avg_resp_time': '|SELECT avg(upstream_response_time) as res',
        '500_num': ' and status:500 | SELECT COUNT(*) as res',
        'sum_resp_time': '| SELECT sum(upstream_response_time) as res'
    }
    THRESHOLD_500 = 0.2
    THRESHOLD_FAIL = 0.9
    QUERY_LIST = []
    ALERTED_USER_LIST = ['382365209@qq.com', '644513759@qq.com']
    END_TIME = None

    @classmethod
    def get_query_is(cls, file_path):
        """
        :param file_path: 一个带有api接口的文件路径
        :return: 返回一个tuple的列表 [(query_condition, condition_name),...]
        query_condition是阿里云日志服务相应的查询条件，即query字符串，condition_name是该str变量名字，按照接口路径和请求方式命名：
        eg. ('request_uri:/api/sns/v1/lit/user/avatars AND request_method:GET', ALILOG_USER_AVATARS)
            ('request_uri:/api/sns/v1/lit/user/info AND request_method:POST',ALILOG_USER_INFO_P)
        """
        res = [('*', 'ALL', 'all_uri', False)]
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
    def ensure_cache(cls):
        """确保QUERY_LIST被缓存"""
        if not cls.QUERY_LIST:
            cls.QUERY_LIST = cls.get_query_from_files(cls.FILE_SET)
        return cls.QUERY_LIST

    @classmethod
    def get_res(cls, base_query, stat_item, start_time, end_time):
        """
        根据输入的query，找出litatomstore近一分钟的日志；由于要直接做分析，所以调用get_log_atom接口，结果总数不能超过1000000
        :param query:
        :return:一个GetLogsResponse对象
        """
        if stat_item not in cls.STAT_ANALYSIS:
            return 0
        resp = AliLogService.get_log_atom(project='litatom', logstore='litatomstore',
                                          query=base_query + cls.STAT_ANALYSIS[stat_item],
                                          from_time=AliLogService.datetime_to_alitime(start_time),
                                          to_time=AliLogService.datetime_to_alitime(end_time))
        res = 0
        try:
            for log in resp.logs:
                contents = log.get_contents()
                res = contents['res']
                if not res or res == 'null':
                    res = 0
        except AttributeError or KeyError or ValueError:
            res = 0
        finally:
            return float(res)

    @classmethod
    def put_stat_2_alilog(cls, name, start_time, end_time, rate_500, avg_resp_time, called_num, avg_status, uri,
                          is_post):
        contents = [('from_time', AliLogService.datetime_to_alitime(start_time)), ('request_uri', uri),
                    ('500_rate', rate_500),
                    ('to_time', AliLogService.datetime_to_alitime(end_time)), ('avg_status', str(avg_status)),
                    ('avg_response_time', str(avg_resp_time)), ('called_num', str(called_num))]
        if is_post:
            contents.append(('request_method', 'POST'))
        else:
            contents.append(('request_method', 'GET'))
        AliLogService.put_logs(contents, project='litatommonitor', logstore='up-res-time-monitor', topic=name)

    @classmethod
    def monitor_online(cls):
        query_list = cls.ensure_cache()
        end_time = datetime.now() if not cls.END_TIME else cls.END_TIME
        start_time = end_time + timedelta(minutes=-1)
        fail_list = []
        list_500 = []
        for query, name, uri, is_post in query_list:
            called_num = cls.get_res(query, 'called_num', start_time, end_time)
            num_500 = cls.get_res(query, '500_num', start_time, end_time)
            if called_num:
                rate_500 = num_500 / called_num
            else:
                rate_500 = 0
            if rate_500 >= cls.THRESHOLD_FAIL:
                fail_list.append([name, rate_500, num_500, called_num, uri])
            elif rate_500 >= cls.THRESHOLD_500:
                list_500.append([name, rate_500, num_500, called_num, uri])
        if fail_list:
            AlertService.send_mail(cls.ALERTED_USER_LIST, str(fail_list), 'FAIL-API-ALERT')
        if list_500:
            AlertService.send_mail(cls.ALERTED_USER_LIST, str(list_500), '500-API-ALERT')

    @classmethod
    def monitor_report(cls, start_time=None, end_time=None):
        query_list = cls.get_query_from_files(cls.FILE_SET)
        end_time = datetime.now() if not end_time else end_time
        start_time = end_time + timedelta(minutes=-1) if not start_time else start_time
        res = []
        total_sum_resp_time = 0
        total_avg_resp_time = 0
        for query, name, uri, is_post in query_list:
            called_num = cls.get_res(query, 'called_num', start_time, end_time)
            if called_num == 0:
                res.append([name, 0, 0, 0, 0, 0, uri])
                continue
            avg_resp_time = cls.get_res(query, 'avg_resp_time', start_time, end_time)
            avg_status = cls.get_res(query, 'avg_status', start_time, end_time)
            num_500 = cls.get_res(query, '500_num', start_time, end_time)
            sum_resp_time = cls.get_res(query, 'sum_resp_time', start_time, end_time)
            if name == 'ALL':
                weight = 1
                total_sum_resp_time = sum_resp_time
                total_avg_resp_time = avg_resp_time
                expect_improvement = 0
            else:
                weight = sum_resp_time / total_sum_resp_time
                if avg_resp_time > total_avg_resp_time:
                    expect_improvement = (avg_resp_time - total_avg_resp_time) * called_num
                else:
                    expect_improvement = 0
            res.append(
                [name, expect_improvement, weight, avg_resp_time, called_num, num_500 / called_num, avg_status, uri])
        return res

    @classmethod
    def output_report(cls, addr, start_time=None, end_time=None):
        res = cls.monitor_report(start_time, end_time)
        res.sort(key=lambda x: x[1], reverse=True)
        write_data_to_xls(addr, ['接口名', '优化期望', '调用时长权重', '平均访问时长', '调用次数', '500比率', '平均状态码', 'uri'], res)
    #
    # @classmethod
    # def find_diff(cls, compared_time=None):
    #     '''
    #     寻找两个时间段之间的接口的调用的时间差 结果集 【接口 第一平均时间 第二平均时间 %time_added  】
    #     :return:
    #     '''
    #     now_res = {}
    #     end_time = datetime.now() if not cls.END_TIME else cls.END_TIME
    #     start_time = end_time + timedelta(minutes=-1)
    #     query_list = cls.get_query_from_files(cls.FILE_SET)
    #     for query, name, uri, is_post in query_list:
    #         logs = cls.fetch_log(query + cls.QUERY_ANALYSIS, start_time, end_time)
    #         # avg_resp_time, called_num, error_rate, status_num = cls.accum_stat(resp_set)
    #         avg_response_time, called_num, avg_status = cls.read_stat(logs)
    #         if avg_response_time == 'null':
    #             continue
    #         print(query, avg_response_time, called_num, avg_status)
    #         now_res[uri] = [float(avg_response_time), int(called_num)]
    #     before_res = {}
    #     cls.END_TIME = parse_standard_time(compared_time) if compared_time else datetime.now() - timedelta(days=29)
    #     for query, name, uri, is_post in query_list:
    #         logs = cls.fetch_log(query + cls.QUERY_ANALYSIS, start_time, end_time)
    #         avg_response_time, called_num, avg_status = cls.read_stat(logs)
    #         if avg_response_time == 'null':
    #             continue
    #         before_res[uri] = [float(avg_response_time), int(called_num)]
    #     for k in now_res:
    #         if k not in before_res:
    #             continue
    #         avg_response_time, now_num = now_res[k]
    #         before_rsp_time, before_num = before_res[k]
    #         print('{:40s} {:10f} {:10f} {:10f}, {:10f}'.format(k, avg_response_time, before_rsp_time, (
    #                 avg_response_time - before_rsp_time) / before_rsp_time * 100,
    #                                                            (avg_response_time - before_rsp_time) * now_num),
    #               now_num)
