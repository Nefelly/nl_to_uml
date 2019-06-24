import os
import time
import sys
import fcntl
from litatom.mq import (
    MQProducer,
    MQConsumer
)
from litatom.service import (
    FeedService
)
from hendrix.conf import setting


class ConsumeFeed(MQConsumer):
    def callback(self, msg):
        payload = msg.get('payload', {})
        feed_id = payload.get('feed_id')
        FeedService.consume_feed_removed(feed_id)
        print payload

def feed_consum():
    queue_name = 'feed_consumed'
    routing_key = 'tasks'
    ConsumeFeed(queue_name,
                routing_key,
                setting.DEFAULT_MQ_HOST,
                setting.DEFAULT_MQ_PORT,
                setting.DEFAULT_MQ_PRODUCER,
                setting.DEFAULT_MQ_PRODUCER_PASSWORD,
                exchange=FeedService.REMOVE_EXCHANGE,
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

if __name__ == "__main__":
    run()