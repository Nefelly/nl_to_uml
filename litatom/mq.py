# coding: utf-8
import logging
import json
import pika
import time
from pika_pool import QueuedPool
from litatom.service import AliLogService
logger = logging.getLogger(__name__)

pool = None


class MQProducer(object):
    """The rabbitmq producer class.
    THIS IS COPIED FROM HENDRIX FOR CUSTOMIZE SETTINGS!

    :param routing_key: the routing_key of message.
    :param host: host of mq.
    :param port: port of mq.
    :param producer: account's username for mq.
    :param producer_password: account' password for mq.
    :param exchange: exchange the message publish to. Default is sns_message.
    :param vhost: the vhost the message published to. Default is vhost01.
    """
    def __init__(self, routing_key, host,
                 port, producer, producer_password,
                 exchange='litatom_message', vhost='/',
                 ignore_err=True):
        self.routing_key = routing_key
        self.host = host
        self.port = port
        self.producer = producer
        self.producer_password = producer_password
        self.exchange = exchange
        self.vhost = vhost
        self.ignore_err = ignore_err
        self.properties = pika.BasicProperties(
            content_type='text/plain',
            delivery_mode=1
        )
        global pool
        if not pool:
            self.__init_pool()

    def __init_pool(self):
        global pool
        credentials = pika.PlainCredentials(
            self.producer,
            self.producer_password
        )
        parameters = pika.ConnectionParameters(
            self.host,
            self.port,
            self.vhost,
            credentials,
            connection_attempts=3,
            retry_delay=0.1,
        )
        pool = QueuedPool(
            create=lambda: pika.BlockingConnection(parameters),
            recycle=None,
            max_size=50,
            max_overflow=15,
            timeout=0.3,
        )
        with pool.acquire() as cxn:
            cxn.channel.exchange_declare(
                exchange=self.exchange,
                exchange_type='direct',
                passive=False,
                durable=True,
                auto_delete=False,
            )

    def publish(self, payload):
        """publish json message.
        Publish json format message.

        :param payload: the json format message to publish.
        """
        global pool

        def send():
            with pool.acquire() as cxn:
                now = time.time()
                message = json.dumps({
                    'payload': payload,
                    'ts': int(now),
                    'mts': int(now * 1000)
                })
                cxn.channel.basic_publish(
                    exchange=self.exchange,
                    routing_key=self.routing_key,
                    body=message,
                    properties=self.properties
                )
        try:
            send()
        except Exception, e:
            print e
            # logger.info('retry publish rabbitmq message caused by: %r', e)
            try:
                send()
            except Exception, e:
                print e
                # logger.exception('Publish rabbitmq message faild')
                if not self.ignore_err:
                    raise


class MQConsumer(object):
    """The rabbit consummer base class.
    THIS IS COPIED FROM HENDRIX FOR CUSTOMIZE SETTINGS!

    :param queue: the queue name the consumer to use.
    :param routing_key: the routing key the queue bind to.
    :param host: host of mq.
    :param port: port of mq.
    :param consumer: account's consumer for mq.
    :param consumer_password: account' password for mq.
    :param no_ack: to turn of message acknowledgments, Default is True.
    :param durable: is the queue durable, Default is False.
    :param exchange: the rabbit exchange to use, Default is sns_exchange.
    :param vhost: the rabbit vhost to use, Default is vhost01.
    """
    def __init__(self, queue, routing_key, host, port, consumer, consumer_password,
                 no_ack=True, durable=False,
                 exchange='litatom_message', vhost='/'):
        self.routing_key = routing_key
        self.queue = queue
        self.host = host
        self.port = port
        self.consumer = consumer
        self.consumer_password = consumer_password
        self.exchange = exchange
        self.vhost = vhost
        self.no_ack = no_ack
        self.durable = durable

    def _get_channel(self):
        credentials = pika.PlainCredentials(self.consumer,
                                            self.consumer_password)
        parameters = pika.ConnectionParameters(
            self.host,
            self.port,
            self.vhost,
            credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.exchange_declare(
            exchange=self.exchange,
            exchange_type='direct',
            passive=False,
            durable=True,
            auto_delete=False,
        )
        return channel

    def callback(self, message):
        """The callback function you need to implement.

        :param message: the json format message received.
        """
        pass


    def start(self):
        """start the consummer"""
        def on_message(channel, method, properties, body):
            try:
                message = json.loads(body)
                self.callback(message)
            except Exception, e:
                logger.error('callback Exception: %s' % str(e))
            if not self.no_ack:
                channel.basic_ack(delivery_tag=method.delivery_tag)
        while True:
            try:
                channel = self._get_channel()
                channel.queue_declare(
                    queue=self.queue,
                    durable=self.durable,
                    exclusive=False,
                    auto_delete=False
                )
                channel.queue_bind(
                    queue=self.queue,
                    exchange=self.exchange,
                    routing_key=self.routing_key,
                )
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(on_message, queue=self.queue,
                                      no_ack=self.no_ack)
                channel.start_consuming()
            except Exception, e:
                logger.error('consumer error routing_key:%s, err: %s' %
                             (self.routing_key, str(e)))
                time.sleep(5)
