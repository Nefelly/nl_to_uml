import sys
import fcntl
import json
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
                    # payload中是通用形式的log表示，需转化为logItemList类型，再进行上传
                    logitemList = []
                    normal_logitem_list = payload['logitemslist']
                    for normal_logitem in normal_logitem_list:
                        logItem = LogItem()
                        logItem.set_time(normal_logitem[0])
                        logItem.set_contents(normal_logitem[1])
                        logitemList.append(logItem)
                    AliLogService.put_logs_atom(logitemList, payload['project'], payload['logstore'],
                                                payload['topic'], payload['source'])

                ConsumeAliLog.insert_pack = []
                ConsumeAliLog.num = 0
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(e)


def ali_log_consume():
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


if __name__ == "__main__":
    run()
