# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2015-2016 VMware, Inc. All Rights Reserved.                    #
#                                                                             #
#  Licensed under the BSD 2-Clause License (the “License”); you may not use   #
#  this file except in compliance with the License.                           #
#                                                                             #
#  The BSD 2-Clause License                                                   #
#                                                                             #
#  Redistribution and use in source and binary forms, with or without         #
#  modification, are permitted provided that the following conditions are met:#
#                                                                             #
#  - Redistributions of source code must retain the above copyright notice,   #
#      this list of conditions and the following disclaimer.                  #
#                                                                             #
#  - Redistributions in binary form must reproduce the above copyright        #
#      notice, this list of conditions and the following disclaimer in the    #
#      documentation and/or other materials provided with the distribution.   #
#                                                                             #
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"#
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE  #
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE #
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE  #
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR        #
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF       #
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS   #
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN    #
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)    #
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF     #
#  THE POSSIBILITY OF SUCH DAMAGE.                                            #
# ----------------------------------------------------------------------------#

import logging
import os
import ssl
from numbers import Number
from threading import Thread

from kombu import Connection, Producer, Exchange, pools, binding
from kombu import Queue as KombuQueue
from kombu.pools import connections
from kombu.mixins import ConsumerMixin

from liota.lib.utilities.utility import systemUUID

log = logging.getLogger(__name__)

PROTOCOL_VERSION = "0.9.1"
# One connection for producer and one for consumer
CONNECTION_POOL_LIMIT = 2
pools.set_limit(CONNECTION_POOL_LIMIT)

EXCHANGE_TYPES = ["direct", "topic", "fanout", "headers"]
DEFAULT_EXCHANGE_TYPE = "topic"
DEFAULT_PUBLISH_PROPERTIES = {"content_type": "application/json",
                              "delivery_mode": 1,
                              "headers": None
                              }

'''
    Utility functions for AMQP
'''


def auto_generate_exchage_name(edge_system_name):
    """
    Auto-generates exchange_name for a given edge_system_name
    :param edge_system_name: EdgeSystemName
    :return: Auto-generated exchange_name
    """
    return "liota.exchange." + systemUUID().get_uuid(edge_system_name)


def auto_generate_routing_key(edge_system_name, for_publish=True):
    """
    Auto-generates routing_key for publisher and consumer for a given edge_system_name
    :param edge_system_name: EdgeSystemName
    :param for_publish: True for publisher and False for consumer
    :return: Auto-generated routing_key
    """
    if for_publish:
        return "liota." + systemUUID().get_uuid(edge_system_name) + ".request"
    else:
        return "liota." + systemUUID().get_uuid(edge_system_name) + ".response"


def auto_generate_queue_name(edge_system_name):
    """
    Auto-generates queue_name for a given edge_system name
    :param edge_system_name: EdgeSystemName
    :return: Auto-generated queue_name
    """
    return "liota.queue." + systemUUID().get_uuid(edge_system_name)


class Amqp:
    """
    AMQP Protocol (version 0.9.1) implementation in LIOTA. It uses Python Kombu library.
    """
    def __init__(self, url, port, identity=None, tls_conf=None, enable_authentication=False,
                 connection_timeout_sec=10):
        """
        :param url: AMQP Broker URL or IP
        :param port: port number of broker
        :param identity: Identity Object
        :param tls_conf: TLSConf object
        :param bool enable_authentication: Enable username/password based authentication or not
        :param connection_timeout_sec: Connection Timeout in seconds
        """
        self.url = url
        self.port = port
        self.identity = identity
        self.tls_conf = tls_conf
        self.enable_authentication = enable_authentication
        self.connection_timeout_sec = connection_timeout_sec
        '''
            From kombu's documentation:
            This is a pool group, which means you give it a connection instance, and you get a pool instance back.
            We have one pool per connection instance to support multiple connections in the same app.
            All connection instances with the same connection parameters will get the same pool.
        '''
        self._connection_pool = None
        '''
            # Separate connection instances for publishing and consuming will be acquired from connection pool.
            # In-case of AMQP broker(ex: RabbitMQ) overload, publishing connection can get blocked for some-time.
            # So, having separate connection for publishing prevents consumers from being blocked.
        '''
        self._publisher_connection = None
        self._consumer_connection = None
        # Single channel for publishing to exchanges
        self._publisher_channel = None
        self._producer = None
        self._consumer = None
        self._init_or_re_init()
        log.info("Initialized AMQP (version {0}) transports".format(PROTOCOL_VERSION))

    def _init_or_re_init(self):
        """
        Initialize or re-initialize connection pool and producer.
        :return:
        """
        self.disconnect()
        self.connect_soc()
        self._initialize_producer()

    def _initialize_producer(self):
        """
        Acquires connection from connection pool for Producer and initializes Producer.
        :return:
        """

        self._publisher_connection = self._connection_pool.acquire()
        # Single publish_channel to publish all metrics from an edge_system
        self._publisher_channel = self._publisher_connection.channel()
        self._producer = Producer(self._publisher_channel)

    def _initialize_consumer_connection(self):
        """
        Acquires connection from connection pool for Consumer
        :return:
        """
        try:
            self._consumer_connection = self._connection_pool.acquire()
        except Exception:
            log.exception("Exception while consume traceback...")
            if self._consumer:
                log.error("Consumer already started..")
                raise Exception("Consumer already started..")

    def connect_soc(self):
        """
        Establishes connection with broker and initializes the connection pool
        :return:
        """
        # Use credentials if authentication is enabled
        if self.enable_authentication:
            if not self.identity.username:
                log.error("Username not found")
                raise ValueError("Username not found")
            elif not self.identity.password:
                log.error("Password not found")
                raise ValueError("Password not found")

        # TLS setup
        if self.tls_conf:
            # Validate CA certificate path
            if self.identity.root_ca_cert:
                if not (os.path.exists(self.identity.root_ca_cert)):
                    log.error("Error : Wrong CA certificate path.")
                    raise ValueError("Error : Wrong CA certificate path.")
            else:
                log.error("Error : Wrong CA certificate path.")
                raise ValueError("Error : CA certificate path is missing")

            # Validate client certificate path
            if self.identity.cert_file:
                if os.path.exists(self.identity.cert_file):
                    client_cert_available = True
                else:
                    log.error("Error : Wrong client certificate path.")
                    raise ValueError("Error : Wrong client certificate path.")
            else:
                client_cert_available = False

            # Validate client key file path
            if self.identity.key_file:
                if os.path.exists(self.identity.key_file):
                    client_key_available = True
                else:
                    log.error("Error : Wrong client key path.")
                    raise ValueError("Error : Wrong client key path.")
            else:
                client_key_available = False

            '''
                Certificate Validations:
                # 1. If client certificate is not present throw error
                # 2. If client key is not present throw error

                If both client certificate and keys are not available, proceed with root CA
            '''

            if not client_cert_available and client_key_available:
                log.error("Error : Client key found, but client certificate not found")
                raise ValueError("Error : Client key found, but client certificate not found")
            if client_cert_available and not client_key_available:
                log.error("Error : Client key found, but client certificate not found")
                raise ValueError("Error : Client certificate found, but client key not found")

            # Setup ssl options
            ssl_details = {'ca_certs': self.identity.root_ca_cert,
                            'certfile': self.identity.cert_file,
                            'keyfile': self.identity.key_file,
                            'cert_reqs': getattr(ssl, self.tls_conf.cert_required),
                            'ssl_version': getattr(ssl, self.tls_conf.tls_version),
                            'ciphers': self.tls_conf.cipher}

        try:

            '''
                Establish connection with one of the following:
                a) Certificate based authorization
                b) Certificate based authorization and username/password based authentication
                c) Username/password based authentication
                d) Plain AMQP
            '''
            amqp_connection = Connection(hostname=self.url, port=self.port, transport="pyamqp",
                                         userid=self.identity.username if self.enable_authentication else None,
                                         password=self.identity.password if self.enable_authentication else None,
                                         ssl=ssl_details if self.tls_conf else False,
                                         connect_timeout=self.connection_timeout_sec)

            self._connection_pool = connections[amqp_connection]

        except Exception, e:
            log.exception("AMQP connection exception traceback..")
            raise e

    def declare_publish_exchange(self, pub_msg_attr):
        """
        Declares an Exchange to which messages will be published.

        :param pub_msg_attr: AmqpPublishMessagingAttributes
        :return:
        """

        if not isinstance(pub_msg_attr, AmqpPublishMessagingAttributes):
            log.error("pub_msg_attr must be of type AmqpPublishMessagingAttributes")
            raise TypeError("pub_msg_attr must be of type AmqpPublishMessagingAttributes")

        exchange = Exchange(name=pub_msg_attr.exchange_name, type=pub_msg_attr.exchange_type)
        # binding exchange with channel
        exchange.durable = pub_msg_attr.exchange_durable
        # delivery_mode at exchange level is transient
        # However, publishers can publish messages with delivery_mode persistent
        exchange.delivery_mode = 1
        bound_exchange = exchange(self._publisher_channel)
        # declaring exchange on broker
        bound_exchange.declare()
        pub_msg_attr.is_exchange_declared = True

        log.info("Declared Exchange: Name: {0}, Type: {1}, Durability: {2}".
                 format(pub_msg_attr.exchange_name, pub_msg_attr.exchange_type, pub_msg_attr.exchange_durable))

    def publish(self, exchange_name, routing_key, message, properties=DEFAULT_PUBLISH_PROPERTIES):
        """
        Published message to the broker.

        :param exchange_name: Exchange name
        :type exchange_name: str or unicode
        :param routing_key: Routing key for binding
        :type routing_key: str or unicode
        :param message: Message to be published
        :type message: str or unicode
        :param bool exchange_durable: Value to survive exchange on RabbitMQ reboot
        :return:
        """

        try:

            self._producer.publish(body=message, exchange=exchange_name, routing_key=routing_key,
                                   content_type=properties['content_type'],
                                   delivery_mode=properties['delivery_mode'],
                                   headers=properties['headers'])
            log.info("Published to exchange: {0} with routing-key: {1}".format(exchange_name, routing_key))
        except Exception:
            log.exception("AMQP publish exception traceback...")

    def consume(self, consume_msg_attr_list):
        """
        Starts ConsumerWorkerThread if not started already

        :param consume_msg_attr_list: List of AmqpConsumeMessagingAttributes
        :return:
        """

        if not isinstance(consume_msg_attr_list, list):
            log.error("consume_msg_attr_list must be of type list")
            raise TypeError("consume_msg_attr_list must be of type list")

        self._initialize_consumer_connection()
        kombu_queues = []
        callbacks = []
        prefetch_size_list = []
        prefetch_count_list = []

        for consume_msg_attr in consume_msg_attr_list:

            exchange = Exchange(name=consume_msg_attr.exchange_name, type=consume_msg_attr.exchange_type)
            exchange.durable = consume_msg_attr.exchange_durable
            # delivery_mode at exchange level is transient
            # However, publishers can publish messages with delivery_mode persistent
            exchange.delivery_mode = 1

            if not 'headers' == consume_msg_attr.exchange_type:
                kombu_queue = KombuQueue(name=consume_msg_attr.queue_name,
                                         # A queue can be bound with an exchange with one or more routing keys
                                         # creating a binding between exchange and routing_key
                                         bindings=[binding(exchange=exchange, routing_key=_)
                                                   for _ in consume_msg_attr.routing_keys
                                                   ]
                                         )
            else:
                kombu_queue = KombuQueue(name=consume_msg_attr.queue_name,
                                         exchange=exchange,
                                         binding_arguments=consume_msg_attr.header_args
                                         )
            kombu_queue.durable = consume_msg_attr.queue_durable
            kombu_queue.exclusive = consume_msg_attr.queue_exclusive
            kombu_queue.auto_delete = consume_msg_attr.queue_auto_delete
            kombu_queue.no_ack = consume_msg_attr.queue_no_ack

            kombu_queues.append(kombu_queue)
            callbacks.append(consume_msg_attr.callback)
            prefetch_size_list.append(consume_msg_attr.prefetch_size)
            prefetch_count_list.append(consume_msg_attr.prefetch_count)

        self._consumer = ConsumerWorkerThread(self._consumer_connection, kombu_queues, callbacks,
                                              prefetch_size_list, prefetch_count_list)

    def disconnect_consumer(self):
        """
        Stop consumer thread and disconnects consumer connection from Broker
        :return:
        """
        if self._consumer and self._consumer_connection:
            self._consumer.stop()
            self._consumer = None
            self._consumer_connection.release()
            self._consumer_connection = None

    def disconnect_producer(self):
        """
        Disconnects publisher connection from Broker
        :return:
        """
        if self._publisher_connection:
            self._publisher_connection.release()
            self._publisher_connection = None
            self._producer = None

    def disconnect(self):
        """
        Disconnect client from broker
        :return:
        """
        try:
            self.disconnect_producer()
            self.disconnect_consumer()
            pools.reset()
            self._connection_pool = None
        except Exception, e:
            log.exception("AMQP disconnect exception traceback..")
            raise e


class AmqpPublishMessagingAttributes:
    """
    Encapsulates Messaging attributes related to AMQP Publish
    """
    def __init__(self, edge_system_name=None, exchange_name=None, exchange_type=DEFAULT_EXCHANGE_TYPE,
                 exchange_durable=False, routing_key=None, msg_delivery_mode=1, header_args=None):
        """
        :param edge_system_name: EdgeSystem Name.
                                 If provided, exchange_name, routing_keys and queue_name will be auto-generated.

        :param exchange_name: Exchange Name

        :param exchange_type: Exchange Type
                              Supported types are: "direct", "topic", "fanout", "headers"

        :param exchange_durable: Exchange durable or not

        :param routing_key: Used when exchange type is one of "direct", "topic", "fanout"
                            Routing Key based on which a particular message should be routed.

        :param msg_delivery_mode: 1 -> transient
                                  2 -> persistent

        :param header_args: Used when exchange_type is 'headers'
                            Must be of type dict. Queues are bound to this exchange with a table of arguments
                            containing headers and values (optional). A special argument named “x-match” determines the
                            matching algorithm, where “all” implies an AND (all pairs must match) and “any” implies OR
                            (at least one pair must match).
        """
        if edge_system_name:
            self.exchange_name = auto_generate_exchage_name(edge_system_name)
            self.routing_key = auto_generate_routing_key(edge_system_name, for_publish=True)
            log.info("Auto-generated exchange_name: {0} and routing_key: {1}".
                     format(self.exchange_name, self.routing_key))
        else:
            # routing_key can be None for exchange of type 'headers'
            if not 'headers' == exchange_type and routing_key is None:
                log.error("routing_key must be non empty character sequence for exchange types other than 'headers'")
                raise ValueError("routing_key must be non empty character sequence"
                                 " for exchange types other than 'headers'")

            self.exchange_name = exchange_name
            self.routing_key = routing_key

        if exchange_type not in EXCHANGE_TYPES:
            log.error("Unsupported exchange-type: {0}".format(str(exchange_type)))
            raise TypeError("Unsupported exchange-type: {0}".format(str(exchange_type)))

        if 'headers' == exchange_type and not isinstance(header_args, dict):
            log.error("For exchange_type `headers`, header_args must be of type dict")
            raise ValueError("For exchange_type `headers`, header_args must be of type dict")

        if not isinstance(msg_delivery_mode, Number) or msg_delivery_mode not in range(1, 3):
            log.error("msg_delivery_mode must be a Number (1 or 2)")
            raise ValueError("msg_delivery_mode must be a Number (1 or 2)")

        self.exchange_type = exchange_type
        # Exchange should survive broker reboot or not
        self.exchange_durable = exchange_durable
        # Exchange declared or not
        self.is_exchange_declared = False

        if self.exchange_name is None:
            # Since exchange_name is None, exchange declared at edge_system level will be used.
            # Hence, marking exchange as declared.
            # Mode 2: Single exchange and different routing-keys for metrics published from an edge_system
            log.warn("exchange_name is None. exchange declared at edge_system level will be used")
            self.is_exchange_declared = True

        self.properties = DEFAULT_PUBLISH_PROPERTIES

        if 2 == msg_delivery_mode:
            self.properties["delivery_mode"] = 2
        if header_args is not None:
            self.properties["headers"] = header_args


class AmqpConsumeMessagingAttributes:
    """
    Encapsulates Messaging attributes related to AMQP Consume
    """
    def __init__(self, edge_system_name=None, exchange_name=None, exchange_type=DEFAULT_EXCHANGE_TYPE,
                 exchange_durable=False, queue_name=None, queue_durable=False, queue_auto_delete=True,
                 queue_exclusive=False, routing_keys=None, queue_no_ack=False, prefetch_size=0, prefetch_count=0,
                 callback=None, header_args=None):
        """
        :param edge_system_name: EdgeSystem Name.
                                 If provided, exchange_name, routing_keys and queue_name will be auto-generated.

        :param exchange_name: Exchange Name

        :param exchange_type: Exchange Type
                              Supported types are: "direct", "topic", "fanout", "headers"

        :param exchange_durable: Exchange durable or not

        :param queue_name: Queue Name.
                           Will be auto-generated if edge_system_name is provided. If edge_system_name is not provided,
                           users have choice to provide their own queue name or leave it to the AMQP broker to assign
                           and auto-generated name

        :param queue_durable: Queue durable or not.
        :param queue_auto_delete: Queue auto-delete or not.
        :param queue_exclusive: Queue exclusive or not

        :param routing_keys: List of routing keys.
                             A queue can be bound with an exchange with one or more routing keys
                             Used when exchange type is one of "direct", "topic", "fanout".

        :param queue_no_ack: Queue should expect ACK or not

        :param prefetch_size: Specify the prefetch window in octets. The server will send a message in advance if it is
                              equal to or smaller in size than the available prefetch size (and also falls within other
                              prefetch limits). May be set to zero, meaning “no specific limit”, although other prefetch
                              limits may still apply.

        :param prefetch_count: Specify the prefetch window in terms of whole messages

        :param callback: Callback method to be invoked.
                         Method's signature must be method(body, message)
                            body -> message body
                            message -> kombu Message object

        :param header_args: Used when exchange_type is 'headers'
                            Must be of type dict. Queues are bound to this exchange with a table of arguments
                            containing headers and values (optional). A special argument named “x-match” determines the
                            matching algorithm, where “all” implies an AND (all pairs must match) and “any” implies OR
                            (at least one pair must match).
        """
        if edge_system_name:
            self.exchange_name = auto_generate_exchage_name(edge_system_name)
            self.routing_keys = [auto_generate_routing_key(edge_system_name, for_publish=False)]
            self.queue_name = auto_generate_queue_name(edge_system_name)
            log.info("Auto-generated exchange_name: {0}, routing_keys: {1} and queue_name: {2}".
                     format(self.exchange_name, str(self.routing_keys), self.queue_name))
        else:
            if not 'headers' == exchange_type and routing_keys is None:
                log.error("routing_key must be non empty character sequence for exchange types other than 'headers'")
                raise ValueError("routing_key must be non empty character sequence"
                                 " for exchange types other than 'headers'")

            if 'headers' == exchange_type and not isinstance(header_args, dict):
                log.error("For exchange_type `headers`, header_args must be of type dict")
                raise ValueError("For exchange_type `headers`, header_args must be of type dict")

            routing_keys = routing_keys if routing_keys else []

            if not isinstance(routing_keys, list):
                log.error("routing_keys must be of type list")
                raise TypeError("routing_keys must be of type list")

            self.exchange_name = exchange_name
            self.routing_keys = routing_keys
            self.queue_name = queue_name

        if exchange_type not in EXCHANGE_TYPES:
            log.error("Unsupported exchange-type: {0}".format(str(exchange_type)))
            raise TypeError("Unsupported exchange-type: {0}".format(str(exchange_type)))

        self.exchange_type = exchange_type
        self.exchange_durable = exchange_durable
        self.queue_durable = queue_durable
        self.queue_auto_delete = queue_auto_delete
        self.queue_exclusive = queue_exclusive
        self.queue_no_ack = queue_no_ack
        self.prefetch_size = prefetch_size
        self.prefetch_count = prefetch_count
        self.callback = callback
        self.header_args = header_args


class AmqpConsumerWorker(ConsumerMixin):
    """
    Implementation of Kombu's ConsumerMixin class.
    ConsumerMixin.run() is a blocking call and should be invoked from a separate thread.
    """

    def __init__(self, connection, queues, callbacks, prefetch_size_list, prefetch_count_list):
        """
        :param connection: Kombu Connection object
        :param queues: list of Queues to consume from
        :param callbacks: list of callbacks for corresponding queues
        :param prefetch_size_list: list of prefetch_size for Consumers that consume from corresponding queues
        :param prefetch_count_list: list of prefetch_count for Consumers that consume from corresponding queues
        """
        if not isinstance(connection, Connection):
            log.error("connection must be of type: {0}".format(str(type(Connection))))
            raise TypeError("connection must be of type: {0}".format(str(type(Connection))))

        if not isinstance(queues, list) or not isinstance(callbacks, list):
            log.error("queues and connections must be of type list")
            raise TypeError("queues and connections must be of type list")

        # ConsumerMixin class expects 'connection' attribute
        self.connection = connection
        self.queues = queues
        self.callbacks = callbacks if len(callbacks) > 0 else [self.on_message]
        self.prefetch_size_list = prefetch_size_list
        self.prefetch_count_list = prefetch_count_list

    def get_consumers(self, Consumer, channel):
        """
        Implementation of get_consumers() of ConsumerMixin class.
        This method is invoked by ConsumerMixin's internal methods.

        :param Consumer: kombu.Consumer
        :param channel:  kombu.Channel
        :return: list of :class:`kombu.Consumer` instances to use.
        """
        kombu_consumer_list = []
        for _ in range(0, len(self.queues)):

                                    # consumer class expects queues, callbacks and accept as list
            kombu_consumer = Consumer(queues=[self.queues[_]],
                                      # making self.on_message() as callback if callback is None
                                      callbacks=[self.callbacks[_]] if self.callbacks[_] else [self.on_message],
                                      accept=['json', 'pickle', 'msgpack', 'yaml']
                                      )
            kombu_consumer.qos(prefetch_size=self.prefetch_size_list[_],
                               prefetch_count=self.prefetch_count_list[_],
                               apply_global=False
                               )
            kombu_consumer_list.append(kombu_consumer)
        return kombu_consumer_list

    def on_message(self, body, message):
        """
        Default callback method for AMQP Consumers.  It simply logs the message and sends ACK
        This callback will be used if user doesn't provide any callback
        :param body: message body
        :param message: Kombu Message object.
        :return:
        """
        log.info('Got message: {0}'.format(body))
        message.ack()


class ConsumerWorkerThread(Thread):
    """
    WorkerThread for AmqpConsumerWorker.
    This worker cannot inherit from both Thread and ConsumerMixin class because of ConsumerMixin's run().
    """

    def __init__(self, connection, queues, callbacks, prefetch_size_list, prefetch_count_list):
        """
        :param connection: Kombu Connection object
        :param queues: list of Queues to consume from
        :param callbacks: list of callbacks for corresponding queues
        :param prefetch_size_list: list of prefetch_size for Consumers that consume from corresponding queues
        :param prefetch_count_list: list of prefetch_count for Consumers that consume from corresponding queues
        """
        Thread.__init__(self)
        self._connection = connection
        self._queues = queues
        self._callbacks = callbacks
        self._prefetch_size_list = prefetch_size_list
        self._prefetch_count_list = prefetch_count_list
        self.daemon = True
        self._consumer = None
        self.start()

    def run(self):
        """
        run() for ConsumerWorkerThread.  This initializes AmqpConsumerWorker and invokes its run() method.

        This method returns when AmqpConsumerWorker.should_stop is set to True
        :return:
        """
        try:
            self._consumer = AmqpConsumerWorker(self._connection, self._queues, self._callbacks,
                                                self._prefetch_size_list, self._prefetch_count_list)
            self._consumer.run()
            log.info("Started AmqpConsumerWorker...")
        except Exception:
            log.exception("Exception traceback in ConsumerWorkerThread...")
            self.stop()

    def stop(self):
        """
        Stop ConsumerWorkerThread, AmqpConsumerWorker and its associated Consumers
        :return:
        """
        # Stops AmqpConsumerWorker and its associated Consumers
        if self._consumer:
            self._consumer.should_stop = True
            log.info("Stopped AmqpConsumerWorker..")
        else:
            log.info("AmqpConsumerWorker is already stopped..")

