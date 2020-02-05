import os
import time
import sys
import fcntl
import datetime
import threading
from pymongo import MongoClient
from litatom.mq import (
    MQProducer,
    MQConsumer
)
from litatom.service import (
    TrackActionService
)
from litatom.const import (
    USER_ACTION_EXCHANGE
)
from hendrix.conf import setting

conf_m = setting.DB_SETTINGS.get('DB_LIT')
host = conf_m['host']
db = host.split('/')[-1].split('?')[0]

def judge_should_run():
    d = datetime.datetime.now()
    hour = d.hour
    min = d.minute
    now = hour * 60 + min
    low = 9 * 60 + 59
    high = 10 * 60 + 2
    return now <= low or now > high

class ConsumeFeed(MQConsumer):
    insert_pack = []
    num = 0
    judge_num = 50 if not setting.IS_DEV else 1
    def callback(self, msg):
        if not judge_should_run():
            time.sleep(1)
        payload = msg.get('payload', {})
        ConsumeFeed.insert_pack.append(payload)
        ConsumeFeed.num += 1
        try:
            if ConsumeFeed.num >= self.judge_num:
                client = MongoClient(host).get_database(db).user_action
                TrackActionService.pymongo_batch_insert(client, ConsumeFeed.insert_pack)
                # print ConsumeFeed.insert_pack
                ConsumeFeed.insert_pack = []
                ConsumeFeed.num = 0
        except Exception, e:
            import traceback
            traceback.print_exc()
            print str(e)


def feed_consum():
    # print "inininin"
    queue_name = 'user_action_consume'
    routing_key = 'tasks'
    ConsumeFeed(queue_name,
                routing_key,
                setting.DEFAULT_MQ_HOST,
                setting.DEFAULT_MQ_PORT,
                setting.DEFAULT_MQ_PRODUCER,
                setting.DEFAULT_MQ_PRODUCER_PASSWORD,
                exchange=USER_ACTION_EXCHANGE,
                vhost=setting.DEFAULT_MQ_VHOST
                ).start()

def run():
    mutex_f = '/var/run/%s.mutex' % __file__.split('/')[-1].replace('.py', '')
    if setting.IS_DEV:
        mutex_f += 'dev'
    f = open(mutex_f, 'w')
    try:
        fcntl.flock(f,
                    fcntl.LOCK_EX|fcntl.LOCK_NB)
    except:
        print 'program already in run'
        sys.exit(0)
    thread_num = 10
    threads = []
    for i in range(thread_num):
        t = threading.Thread(target=feed_consum, args=())
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    # feed_consum()
    # thread_num = 10
    # threads = []
    # for i in range(thread_num):
    #     t = threading.Thread(target=feed_consum, args=())
    #     t.start()
    #     threads.append(t)
    # for t in threads:
    #     t.join()
    # feed_consum()

if __name__ == "__main__":
    run()