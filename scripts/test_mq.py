import os
import time
import sys
from litatom.mq import (
    MQProducer,
    MQConsumer
)
from hendrix.conf import setting

def test_push():
    try:
        MQProducer(
            'tasks',
            setting.DEFAULT_MQ_HOST,
            setting.DEFAULT_MQ_PORT,
            setting.DEFAULT_MQ_PRODUCER,
            setting.DEFAULT_MQ_PRODUCER_PASSWORD,
            exchange="sms-send-msg",
            vhost=setting.DEFAULT_MQ_VHOST
        ).publish({
            "name": "seller_aaa",
            "feed_id": 'feed_id1',
            "user_id": "00000002"
        })
    except Exception, e:
        print e

class TestConsume(MQConsumer):
    def callback(self, msg):
        payload = msg.get('payload', {})
        print payload

def test_consum():
    queue_name = 'test'
    routing_key = 'tasks'
    TestConsume(queue_name,
                routing_key,
                setting.DEFAULT_MQ_HOST,
                setting.DEFAULT_MQ_PORT,
                setting.DEFAULT_MQ_PRODUCER,
                setting.DEFAULT_MQ_PRODUCER_PASSWORD,
                exchange="sms-send-msg",
                vhost=setting.DEFAULT_MQ_VHOST
                ).start()


if __name__ == "__main__":
    if sys.argv[1] == 'push':
        test_push()
    else:
        test_consum()
