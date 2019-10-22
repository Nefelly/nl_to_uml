import os
import time
import sys
import fcntl
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

uri = setting.DB_SETTINGS.get('DB_LIT')["host"]
print uri
client = MongoClient(uri).get_database('lit').user_action


class ConsumeFeed(MQConsumer):
    insert_pack = []
    num = 0

    def callback(self, msg):
        payload = msg.get('payload', {})
        ConsumeFeed.insert_pack.append(payload)
        ConsumeFeed.num += 1
        print ConsumeFeed.num
        try:
            if ConsumeFeed.num >= 1:
                TrackActionService.pymongo_batch_insert(client, ConsumeFeed.insert_pack)
                print ConsumeFeed.insert_pack
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
    feed_consum()
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