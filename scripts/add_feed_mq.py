import os
import time
import sys
import fcntl
import threading
from litatom.mq import (
    MQProducer,
    MQConsumer
)
from litatom.service import (
    FeedService
)
from litatom.const import (
    ADD_EXCHANGE
)
from hendrix.conf import setting


class ConsumeFeed(MQConsumer):
    def callback(self, msg):
        payload = msg.get('payload', {})
        print(payload)
        feed_id = payload.get('feed_id')
        pics = payload.get('pics', [])
        region_key = payload.get('region_key')
        FeedService.consume_feed_added(feed_id, pics, region_key)


def feed_consum():
    queue_name = 'feed_added'
    routing_key = 'tasks'
    ConsumeFeed(queue_name,
                routing_key,
                setting.DEFAULT_MQ_HOST,
                setting.DEFAULT_MQ_PORT,
                setting.DEFAULT_MQ_PRODUCER,
                setting.DEFAULT_MQ_PRODUCER_PASSWORD,
                exchange=ADD_EXCHANGE,
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

if __name__ == "__main__":
    run()