import os
import time
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
            "name": "seller_category_audit",
            "feed_id": 'feed_id1',
            "user_id": "00000002"
        })
    except Exception, e:
        print e
        logger.exception('Publish fulishe tasks message error')


if __name__ == "__main__":
    test_push()
