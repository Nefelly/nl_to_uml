# coding: utf-8
import logging
from ..redis import RedisClient
from ..mq import (
    MQProducer,
    MQConsumer
)
from hendrix.conf import setting

from ..key import (
    TOKEN_BUCKET_KEY
)
from ..const import ONE_DAY

redis_client = RedisClient()['lit']
logger = logging.getLogger(__name__)

class MqService(object):
    """

    """
    @classmethod
    def push(cls, exchange, payload):
        try:
            MQProducer(
                'tasks',
                setting.DEFAULT_MQ_HOST,
                setting.DEFAULT_MQ_PORT,
                setting.DEFAULT_MQ_PRODUCER,
                setting.DEFAULT_MQ_PRODUCER_PASSWORD,
                exchange=exchange,
                vhost=setting.DEFAULT_MQ_VHOST
            ).publish(payload)
        except Exception, e:
            logging.error(e)


    @classmethod
    def consume(cls, exchange):
        pass