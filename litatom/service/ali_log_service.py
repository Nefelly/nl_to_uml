# coding: utf-8
import json
from time import time
import datetime
import traceback
from aliyun.log import *
from ..util import (
    get_time_int_from_str
)
import logging
from ..const import (
    ONE_DAY
)
from ..redis import RedisClient
from hendrix.conf import setting
from ..const import ALI_LOG_EXCHANGE
from ..mq import MQProducer
from flask import request

from ..util import (
    read_data_from_xls
)

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']


class AliLogService(object):
    '''
    https://help.aliyun.com/document_detail/29077.html?spm=5176.2020520112.0.0.734834c0eZ4Hb2
    '''

    # ENDPOINT = 'cn-hongkong.log.aliyuncs.com'  # 选择与上面步骤创建Project所属区域匹配的Endpoint
    ENDPOINT = 'cn-hongkong-intranet.log.aliyuncs.com'  # 真内网
    ACCESS_KEY_ID = 'LTAI4FmgXZDqyFsLxf6Rez3e'  # 使用您的阿里云访问密钥AccessKeyId
    ACCESS_KEY = 'n6ZOCqP28vfOJi3YbNETJynEG87sRo'  # 使用您的阿里云访问密钥AccessKeySecret
    DEFAULT_PROJECT = 'litatomaction'  # 上面步骤创建的项目名称
    DEFAULT_LOGSTORE = 'litatomactionstore'  # 上面步骤创建的日志库名称
    ONE_LOG_MAX = 400000

    # 重要提示：创建的logstore请配置为4个shard以便于后面测试通过
    # 构建一个client
    DEFAULT_CLIENT = LogClient(ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY)
    DEFAULT_TOPIC = "default_topic"
    DEFAULT_SOURCE = "default_source"  # 日志来源机器ip

    @classmethod
    def datetime_to_alitime(cls, t):
        return t.strftime("%Y-%m-%d %H:%M:%S+8:00")

    @classmethod
    def alitime_to_datetime(cls, ali_time):
        return datetime.datetime.strptime(ali_time, "%Y-%m-%d %H:%M:%S+8:00")

    @classmethod
    def _read_date_from_addr(cls, addr):
        """
        从daily_stat文件地址获取当前日期
        :param addr:
        :return:
        """
        import re
        pattern0 = "/data/statres/"
        res = re.sub(pattern0, '', addr)
        pattern1 = ".xlsx"
        res = re.sub(pattern1, '', res)
        pattern2 = 'ad.xlsx'
        date = re.sub(pattern2, '', res)
        return date

    @classmethod
    def _put_logs_atom(cls, logitemList, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, topic=DEFAULT_TOPIC,
                      source=DEFAULT_SOURCE, client=DEFAULT_CLIENT):
        '''最底层的上传日志服务'''
        if setting.IS_DEV:
            logstore = 'test-lit'
            project = 'test-lit'
        try:
            request = PutLogsRequest(project, logstore, topic, source, logitemList)
            response = client.put_logs(request)
            return response.get_all_headers()
        except Exception as e:
            logger.error('put ali logs error: %s', e)
            # LogItem对象无法json序列化，此处需要转化为一般格式进消息队列
            normal_logitem_list = []
            for logitem in logitemList:
                item_time = logitem.get_time()
                item_content = logitem.get_contents()
                normal_logitem_list.append((item_time, item_content))
            MQProducer(
                'tasks',
                setting.DEFAULT_MQ_HOST,
                setting.DEFAULT_MQ_PORT,
                setting.DEFAULT_MQ_PRODUCER,
                setting.DEFAULT_MQ_PRODUCER_PASSWORD,
                exchange=ALI_LOG_EXCHANGE,
                vhost=setting.DEFAULT_MQ_VHOST
            ).publish({'logitemslist': normal_logitem_list, 'topic': topic, 'source': source, 'project': project,
                       'logstore': logstore})
            return None

    @classmethod
    def put_logs(cls, contents, topic=DEFAULT_TOPIC, source=DEFAULT_SOURCE, project=DEFAULT_PROJECT,
                 logstore=DEFAULT_LOGSTORE, client=DEFAULT_CLIENT):
        """
        上传一条日志，contents格式为[('key','value'),('key2','value2')...]，
        :return: 一个LogSponse对象，为http相应包头部封装后的对象
        """
        logitemList = []  # LogItem list
        logItem = LogItem()
        logItem.set_time(int(time()))
        try:
            if request.platform:
                contents.append(('platform', request.platform))
        except:
            pass
        logItem.set_contents(contents)
        logitemList.append(logItem)
        cls._put_logs_atom(logitemList, project, logstore, topic, source, client)

    @classmethod
    def simplest_put_log(cls, contents, project):
        topic = cls.DEFAULT_TOPIC
        source = cls.DEFAULT_SOURCE
        client = cls.DEFAULT_CLIENT
        logstore = project
        logitemList = []  # LogItem list
        logItem = LogItem()
        logItem.set_time(int(time()))
        logItem.set_contents(contents)
        logitemList.append(logItem)
        cls._put_logs_atom(logitemList, project, logstore, topic, source, client)


    @classmethod
    def put_logs_batch(cls, contents_list, topic=DEFAULT_TOPIC, source=DEFAULT_SOURCE, project=DEFAULT_PROJECT,
                       logstore=DEFAULT_LOGSTORE, client=DEFAULT_CLIENT):
        """
        批量上传日志
        :param contents_list: list[contents1,contents2,....]
        """
        logitemList = []  # LogItem list
        for contents in contents_list:
            logItem = LogItem()
            logItem.set_time(int(time()))
            logItem.set_contents(contents)
            logitemList.append(logItem)
        cls._put_logs_atom(logitemList, project, logstore, topic, source, client)

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
        :param res:
        :param attributes:
        :return:
        """
        if not attributes:
            return res
        for log in res.logs:
            contents = log.get_contents()
            res_contents = {}
            res_contents['__time'] = log.get_time()
            for attribute in attributes:
                if attribute in contents.keys():
                    res_contents[attribute] = contents[attribute]
            log.contents = res_contents.copy()
        return res

    @classmethod
    def get_size(cls, query='*', from_time=int(time() - 3600), to_time=int(time()), project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE):
        if isinstance(from_time, str):
            from_time = get_time_int_from_str(from_time)
        if isinstance(to_time, str):
            to_time = get_time_int_from_str(to_time)
        query = query + '|SELECT COUNT(*) as num'
        res = cls.DEFAULT_CLIENT.get_log(project=project, logstore=logstore, from_time=from_time, to_time=to_time,
                                         size=1, query=query)
        for log in res.logs:
            return int(log.get_contents()['num'])
        return 0


    @classmethod
    def get_loglst(cls, query='*', from_time=int(time() - 3600),
                     to_time=int(time()), project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, save_add = None):
        if isinstance(from_time, str):
            from_time = get_time_int_from_str(from_time)
        if isinstance(to_time, str):
            to_time = get_time_int_from_str(to_time)
        size = cls.get_size(query, from_time, to_time, project, logstore)
        print 'log size', size
        querys = [(from_time, to_time)]
        time_interval = to_time - from_time
        if size > cls.ONE_LOG_MAX:
            querys = []
            loops = size / cls.ONE_LOG_MAX
            if time_interval / ONE_DAY < loops: # 天数少于循环数  高峰期与低谷期的流量差异比较大
                loops *= 10
            else:
                loops *= 5
            time_delta = (to_time - from_time) / loops
            for i in range(loops):
                start_time = from_time + i * time_delta
                end_time = from_time + (i + 1) * time_delta
                querys.append((round(start_time), round(end_time)))
        res = []
        print querys
        fewer_fields = True if size > 10000 and logstore == 'litatomstore' else False
        if fewer_fields:
            print 'we are in fewer'
        f = ''
        if save_add:
            f = open(save_add, 'w')
        cnt = 1
        tmp_contents = []
        for start_time, end_time in querys:
            raw = cls.DEFAULT_CLIENT.get_log(project=project, logstore=logstore, from_time=start_time, to_time=end_time,
                             size=cls.ONE_LOG_MAX, query=query)
            if not save_add:
                for log in raw.logs:
                        contents = log.get_contents()
                        contents['__time'] = log.get_time()
                        if fewer_fields:
                            res.append({'__time': contents['__time'], 'request_uri': contents['request_uri']})
                        else:
                            res.append(contents)
            else:
                for log in raw.logs:
                    contents = log.get_contents()
                    tmp_contents.append(str(log.get_time()) + '\t' + contents['request_uri'])
                    cnt += 1
                    if cnt % 1000 == 0:
                        f.write('\n'.join(tmp_contents))
                        f.flush()
                    import gc
                    gc.collect()
            print start_time, end_time, len(res)
        f.write('\n'.join(tmp_contents))
        return res

    @classmethod
    def get_log_atom(cls, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, from_time=int(time() - 3600),
                     to_time=int(time()), client=DEFAULT_CLIENT, size=1000000, attributes=None, query='*'):
        """
        单次读取一份log
        :return:
        """
        try:
            res = client.get_log(project=project, logstore=logstore, from_time=from_time, to_time=to_time,
                                 size=size, query=query)
        except LogException as e:
            # print(e)
            pass
        else:
            if not attributes:
                return res
            else:
                return cls.select_log_by_attributes(res, attributes)

    @classmethod
    def get_log_by_time_and_topic(cls, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, from_time=int(time() - 3600),
                                  to_time=int(time()), client=DEFAULT_CLIENT, size=1000000, attributes=None, query='*'):
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
        :param size: 最大为1000000
        :return:返回一个GetLogsResponse对象的迭代器，其logs属性为一个QueriedLog列表，每个元素有三个方法get_time(),
        get_source(),get_contents()三个方法获得log内容，contents为json格式
        """
        if size == -1 or size > 400000:
            if isinstance(from_time, int) and isinstance(to_time, int):
                time_delta = (to_time - from_time) / 100.0
                for i in range(100):
                    start_time = from_time + i * time_delta
                    end_time = from_time + (i + 1) * time_delta
                    resp = cls.get_log_atom(project=project, logstore=logstore, from_time=round(start_time),
                                            to_time=round(end_time), size=1000000, query=query, client=client)
                    yield resp
            elif isinstance(from_time, str) and isinstance(to_time, str):
                from_time_date = cls.alitime_to_datetime(from_time)
                to_time_date = cls.alitime_to_datetime(to_time)
                time_delta = (to_time_date - from_time_date) / 100
                for i in range(100):
                    start_time = cls.datetime_to_alitime(from_time_date + i * time_delta)
                    end_time = cls.datetime_to_alitime(from_time_date + (i + 1) * time_delta)
                    resp = cls.get_log_atom(project=project, logstore=logstore, from_time=start_time, to_time=end_time,
                                            size=200000, query=query, client=client)
                    yield resp
        else:
            yield cls.get_log_atom(project=project, logstore=logstore, from_time=from_time, to_time=to_time,
                                   size=size, query=query, client=client)

    @classmethod
    def get_all_log_by_time_and_topic(cls, project=DEFAULT_PROJECT, logstore=DEFAULT_LOGSTORE, client=DEFAULT_CLIENT,
                                      topic=DEFAULT_TOPIC, from_time=int(time() - 3600), to_time=int(time()),
                                      query='*'):
        """
        返回所有的logs，注意此时query语句不能有分析语法，例如select
        :param project:
        :param logstore:
        :param client:
        :param topic:
        :param from_time:
        :param to_time:
        :param query:
        :return:GetLogsResponse的列表,GetLogsResponse是一个结果集，其有logs属性，为一个QueriedLog的列表，还有log_print()方法
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

    @classmethod
    def track_user_ids(cls, add):
        import urlparse
        from ..model import User
        res = set()
        cnt = 0
        for l in open(add).readlines():
            cnt += 1
            if cnt % 1000 == 0:
               print cnt, len(res)
            if not l:
                continue
            result = urlparse.urlparse(l)
            sid = urlparse.parse_qs(result.query)['sid'][0]
            user_id = User.get_user_id_by_session(sid)
            if user_id:
                res.add(user_id)
        return res