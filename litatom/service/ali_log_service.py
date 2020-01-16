# coding: utf-8
import json
import time
import traceback
from aliyun.log import *
import logging
from ..redis import RedisClient

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
    # # list 所有的logstore
    # req1 = ListLogstoresRequest(project)
    # res1 = client.list_logstores(req1)
    # res1.log_print()
    DEFAULT_TOPIC = "default_topic"
    DEFAULT_SOURCE = "default_source"  # 日志来源机器ip

    '''
    上传一条日志，contents格式为[('key','value'),('key2','value2')...]，
    返回一个LogSponse对象，为http相应包头部封装后的对象
    '''

    @classmethod
    def put_logs(cls, contents, topic=DEFAULT_TOPIC, source=DEFAULT_SOURCE, project=DEFAULT_PROJECT,
                 logstore=DEFAULT_LOGSTORE, client=DEFAULT_CLIENT, compress=False):
        logitemList = []  # LogItem list
        logItem = LogItem()
        logItem.set_time(int(time.time()))
        logItem.set_contents(contents)
        logitemList.append(logItem)
        # 包装上传请求并发送
        request = PutLogsRequest(project, logstore, topic, source, logitemList, compress=compress)
        response = client.put_logs(request)
        return response

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
