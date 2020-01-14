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

    @classmethod
    def test(cls):
        endpoint = 'cn-hongkong.log.aliyuncs.com'  # 选择与上面步骤创建Project所属区域匹配的Endpoint
        access_key_id = 'LTAI4FmgXZDqyFsLxf6Rez3e'  # 使用您的阿里云访问密钥AccessKeyId
        access_key = 'n6ZOCqP28vfOJi3YbNETJynEG87sRo'  # 使用您的阿里云访问密钥AccessKeySecret
        project = 'litatomaction'  # 上面步骤创建的项目名称
        logstore = 'litatomactionstore'  # 上面步骤创建的日志库名称

        # 重要提示：创建的logstore请配置为4个shard以便于后面测试通过
        # 构建一个client
        client = LogClient(endpoint, access_key_id, access_key)
        # list 所有的logstore
        req1 = ListLogstoresRequest(project)
        res1 = client.list_logstores(req1)
        res1.log_print()
        topic = "imtopic"
        source = "imsource"

        for i in range(10):
            logitemList = []  # LogItem list
            for j in range(10):
                contents = [('action', 'test'), ('amount', '1'), ('remark', 'hanimei') ]
                logItem = LogItem()
                logItem.set_time(int(time.time()))
                logItem.set_contents(contents)
                logitemList.append(logItem)
            req2 = PutLogsRequest(project, logstore, topic, source, logitemList)
            res2 = client.put_logs(req2)
            print 'hh'