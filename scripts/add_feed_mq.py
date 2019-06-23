import os
import time
import sys
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
        FeedService.consume_feed_added(feed_id)
        print payload

def feed_consum():
    queue_name = 'feed_added'
    routing_key = 'tasks'
    ConsumeFeed(queue_name,
                routing_key,
                setting.DEFAULT_MQ_HOST,
                setting.DEFAULT_MQ_PORT,
                setting.DEFAULT_MQ_PRODUCER,
                setting.DEFAULT_MQ_PRODUCER_PASSWORD,
                exchange=FeedService.EXCHANGE,
                vhost=setting.DEFAULT_MQ_VHOST
                ).start()


if __name__ == "__main__":
   feed_consum()