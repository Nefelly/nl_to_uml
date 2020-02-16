# coding: utf-8
import json
from time import time
import traceback
from aliyun.log import *
import logging
from ..redis import RedisClient
from ..util import (
    read_data_from_xls
)

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']


class AliLogService(object):
    '''
    https://help.aliyun.com/document_detail/29077.html?spm=5176.2020520112.0.0.734834c0eZ4Hb2
    '''

    ENDPOINT = 'cn-hongkong.log.aliyuncs.com'  # 选择与上面步骤创建Project所属区域匹配的Endpoint
    ACCESS_KEY_ID = 'LTAI4FmgXZDqyFsLxf6Rez3e'  # 使用您的阿里云访问密钥AccessKeyId
    ACCESS_KEY = 'n6ZOCqP28vfOJi3YbNETJynEG87sRo'  # 使用您的阿里云访问密钥AccessKeySecret
    DEFAULT_PROJECT = 'litatomaction'  # 上面步骤创建的项目名称
    DEFAULT_LOGSTORE = 'litatomactionstore'  # 上面步骤创建的日志库名称

    # 重要提示：创建的logstore请配置为4个shard以便于后面测试通过
    # 构建一个client
    DEFAULT_CLIENT = LogClient(ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY)
    DEFAULT_TOPIC = "default_topic"
    DEFAULT_SOURCE = "default_source"  # 日志来源机器ip

    '''
    从daily_stat文件地址获取当前日期
    '''

    @classmethod
    def _read_date_from_addr(cls, addr):
        import re
        pattern0 = "/data/statres/"
        res = re.sub(pattern0, '', addr)
        pattern1 = ".xlsx"
        res = re.sub(pattern1, '', res)
        pattern2 = 'ad.xlsx'
        date = re.sub(pattern2, '', res)
        return date

    '''
    上传一条日志，contents格式为[('key','value'),('key2','value2')...]，
    返回一个LogSponse对象，为http相应包头部封装后的对象
    '''

    @classmethod
    def put_logs(cls, contents, topic=DEFAULT_TOPIC, source=DEFAULT_SOURCE, project=DEFAULT_PROJECT,
                 logstore=DEFAULT_LOGSTORE, client=DEFAULT_CLIENT):
        logitemList = []  # LogItem list
        logItem = LogItem()
        logItem.set_time(int(time.time()))
        logItem.set_contents(contents)
        logitemList.append(logItem)
        request = PutLogsRequest(project, logstore, topic, source, logitemList)
        response = client.put_logs(request)
        return response.get_all_headers()

    @classmethod
    def put_daily_stat(cls, contents, topic='undefined'):
        """上传一条日常统计数据日志"""
        cls.put_logs(contents, topic=topic, project='litatommonitor', logstore='daily-stat-monitor')

    # @classmethod
    # def put_dailt_stat_from_xlsx(cls, name):
    #     tb_header, tb_data = read_data_from_xls(name)
    #     contents = [('date', cls._read_date_from_addr(name))]
    #     nstat = len(tb_data)
    #     for stat in range(nstat):
    #         for col in range(tb_data[0]):
    #             contents += [(tb_header[col], tb_data[stat+1][col])]

    @classmethod
    def select_log_by_attributes(cls, res, attributes):
        """
        筛选logs，投影到特定的属性（组）上，
        :param logs:
        :param attributes:
        :return:
        """
        if not attributes:
            return res
        for log in res.logs:
            contents = log.get_contents()
            res_contents = {}
            for attribute in attributes:
                if attribute in contents.keys():
                    res_contents[attribute] = contents[attribute]
            log.contents = res_contents.copy()
        return res

    @classmethod
    def get_log_by_time(cls, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, from_time=int(time() - 3600),
                        to_time=int(time()), client=DEFAULT_CLIENT, size=-1, attributes=None, query='*'):
        """
        仅通过时间筛选某logstore中的log
        :param query:
        :param attributes: 需要select出来的属性，默认None表示所有属性，['attr1','attr2',...]
        :param project:
        :param logstore:
        :param from_time: the begin timestamp or format of time in readable time
        like "%Y-%m-%d %H:%M:%S<time_zone>" e.g. "2018-01-02 12:12:10+8:00", also support human readable string,
        e.g. "1 hour ago", "now", "yesterday 0:0:0"
        :param to_time:
        :param client:
        :param size: 默认为-1， 即无limit
        :return:返回一个GetLogsResponse对象，其logs属性为一个QueriedLog列表，每个元素有三个方法get_time(),get_source(),
                get_contents()三个方法获得log内容，contents为json格式
        """
        try:
            res = client.get_log(project=project, logstore=logstore, from_time=from_time, to_time=to_time, size=size,
                                 query=query)
        except LogException as e:
            print(e)
        else:
            if not attributes:
                return res
            else:
                selected_res = cls.select_log_by_attributes(res, attributes)
                return selected_res

    @classmethod
    def get_log_by_time_and_topic(cls, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, topic=DEFAULT_TOPIC,
                                  query='*',
                                  from_time=int(time() - 3600), to_time=int(time()), line=-1, client=DEFAULT_CLIENT):
        """
        通过time和topic筛选某logstore中的log
        :param line:
        :param project:
        :param logstore:
        :param topic:
        :param from_time:
        :param to_time:
        :param client:
        :return: 返回一个QueriedLog列表，每个元素有三个方法get_time(),get_source(),get_contents()三个方法获得log内容，contents为json格式
        """
        request = GetLogsRequest(project=project, logstore=logstore, fromTime=from_time, toTime=to_time, topic=topic,
                                 query=query, line=line)
        res = client.get_logs(request)
        return res

    @classmethod
    def get_all_log_by_time_and_topic(cls, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, client=DEFAULT_CLIENT,
                                      topic=DEFAULT_TOPIC, from_time=int(time() - 3600), to_time=int(time()),
                                      query='*'):
        """
        返回所有的logs
        :param project:
        :param logstore:
        :param client:
        :param topic:
        :param from_time:
        :param to_time:
        :param query:
        :return:GetLogsResponse的列表,GetLogsResponse是一个结果集，其有logs属性，为一个QueriedLog的列表
        """
        res = client.get_log_all(project=project, logstore=logstore, topic=topic, from_time=from_time, to_time=to_time,
                                 query=query)
        return res

    @classmethod
    def get_histogram_by_time_and_topic(cls, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, topic=DEFAULT_TOPIC,
                                        from_time=int(time() - 3600), to_time=int(time()), query='*',
                                        client=DEFAULT_CLIENT):
        """
        通过time和topic绘制某logstore中log的直方图
        :param project:
        :param logstore:
        :param topic:
        :param from_time:
        :param to_time:
        :param query:
        :return:
        """
        req = GetHistogramsRequest(project=project, logstore=logstore, fromTime=from_time, toTime=to_time, topic=topic,
                                   query=query)
        res = client.get_histograms(req)
        return res

    # @classmethod
    # def pull_logs(cls, client=DEFAULT_CLIENT, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, compress=False):
    #     res = client.get_cursor(project, logstore, 0, int(time.time() - 60))
    #     res.log_print()
    #     cursor = res.get_cursor()
    #
    #     res = client.pull_logs(project, logstore, 0, cursor, 1, compress=compress)
    #     res.log_print()
    #
    #     # test readable start time
    #     res = client.get_cursor(project, logstore, 0,
    #                             datetime.fromtimestamp(int(time.time() - 60)).strftime('%Y-%m-%d %H:%M:%S'))
    #     res.log_print()
    #
    #     # test pull_log
    #     res = client.pull_log(project, logstore, 0,
    #                           datetime.fromtimestamp(int(time.time() - 60)).strftime('%Y-%m-%d %H:%M:%S'),
    #                           datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'))
    #     for x in res:
    #         x.log_print()

    # # list 所有的logstore
    # req1 = ListLogstoresRequest(project)
    # res1 = client.list_logstores(req1)
    # res1.log_print()
