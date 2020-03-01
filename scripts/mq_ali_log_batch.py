import sys
import fcntl
from aliyun.log import *
from time import time
import threading
from litatom.mq import (
    MQProducer,
    MQConsumer
)
from litatom.service import (
    AliLogService
)
from litatom.const import (
    ALI_LOG_EXCHANGE
)
from hendrix.conf import setting


class ConsumeAliLog(MQConsumer):
    insert_pack = []
    num = 0
    judge_num = 50 if not setting.IS_DEV else 1

    def callback(self, msg):
        payload = msg.get('payload', {})
        ConsumeAliLog.insert_pack.append(payload)
        ConsumeAliLog.num += 1
        try:
            if ConsumeAliLog.num >= self.judge_num:
                for payload in ConsumeAliLog.insert_pack:
                    AliLogService.put_logs_atom(payload['logitemslist'], payload['project'], payload['logstore'],
                                                payload['topic'], payload['source'], payload['client'])

                ConsumeAliLog.insert_pack = []
                ConsumeAliLog.num = 0
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(e)


def ali_log_consume():
    # print "inininin"
    queue_name = 'put_ali_log_consume'
    routing_key = 'tasks'
    ConsumeAliLog(queue_name,
                  routing_key,
                  setting.DEFAULT_MQ_HOST,
                  setting.DEFAULT_MQ_PORT,
                  setting.DEFAULT_MQ_PRODUCER,
                  setting.DEFAULT_MQ_PRODUCER_PASSWORD,
                  exchange=ALI_LOG_EXCHANGE,
                  vhost=setting.DEFAULT_MQ_VHOST
                  ).start()


def run():
    mutex_f = '/var/run/%s.mutex' % __file__.split('/')[-1].replace('.py', '')
    if setting.IS_DEV:
        mutex_f += 'dev'
    f = open(mutex_f, 'w')
    try:
        fcntl.flock(f,
                    fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception as e:
        print('program already in run')
        sys.exit(0)
    thread_num = 10
    threads = []
    for i in range(thread_num):
        t = threading.Thread(target=ali_log_consume, args=())
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


def test_push():
    ENDPOINT = 'cn-hongkong.log.aliyuncs.com'  # 选择与上面步骤创建Project所属区域匹配的Endpoint
    ACCESS_KEY_ID = 'LTAI4FmgXZDqyFsLxf6Rez3e'  # 使用您的阿里云访问密钥AccessKeyId
    ACCESS_KEY = 'n6ZOCqP28vfOJi3YbNETJynEG87sRo'  # 使用您的阿里云访问密钥AccessKeySecret
    logitemList = []  # LogItem list
    for i in range(30):
        logItem = LogItem()
        logItem.set_time(int(time()))
        logItem.set_contents([(str(i + 1), 'test_log' + str(i + 1))])
        logitemList.append(logItem)

    MQProducer(
        'tasks',
        setting.DEFAULT_MQ_HOST,
        setting.DEFAULT_MQ_PORT,
        setting.DEFAULT_MQ_PRODUCER,
        setting.DEFAULT_MQ_PRODUCER_PASSWORD,
        exchange=ALI_LOG_EXCHANGE,
        vhost=setting.DEFAULT_MQ_VHOST
    ).publish({'logitemslist': logitemList, 'topic': 'test', 'source': 'default_source', 'project': 'litatommonitor',
               'logstore': 'daily-stat-monitor', 'client': LogClient(ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY)})


if __name__ == "__main__":
    if sys.argv[1] == 'push':
        test_push()
    else:
        run()
