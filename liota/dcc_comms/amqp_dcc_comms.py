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

from liota.dcc_comms.dcc_comms import DCCComms
from liota.lib.transports.amqp import Amqp, AmqpPublishMessagingAttributes, AmqpConsumeMessagingAttributes
from liota.lib.utilities.utility import store_edge_system_uuid, systemUUID

log = logging.getLogger(__name__)


class AmqpDccComms(DCCComms):
    """
    DccComms for AMQP Transport
    """

    def __init__(self, edge_system_name, url, port, identity=None, tls_conf=None,
                 amqp_pub_msg_attr=None, enable_authentication=False, connection_timeout_sec=10):
        """
        Initializes AMQP transports and declares publish exchange for an edge_system.
        AMQPPublishMessagingAttributes for this publish exchange is either auto-generated or provided by the user

        :param url: AMQP Broker URL or IP
        :param port: port number of broker
        :param identity: Identity Object
        :param tls_conf: TLSConf object
        :param qos_details: QoSDetails object
        :param bool enable_authentication: Enable username/password based authentication or not
        """
        self.edge_system_name = edge_system_name
        self.url = url
        self.port = port
        self.client = None
        self.identity = identity
        self.tls_conf = tls_conf
        self.enable_authentication = enable_authentication
        self.connection_timeout_sec = connection_timeout_sec

        if amqp_pub_msg_attr is None:
            # auto-generate routing key and exchange_name
            self.pub_msg_attr = AmqpPublishMessagingAttributes(self.edge_system_name)
            #  Storing edge_system name and generated local_uuid which will be used in auto-generation of pub-sub topic
            store_edge_system_uuid(entity_name=self.edge_system_name,
                                   entity_id=systemUUID().get_uuid(self.edge_system_name),
                                   reg_entity_id=None)
        elif isinstance(amqp_pub_msg_attr, AmqpPublishMessagingAttributes):
            self.pub_msg_attr = amqp_pub_msg_attr
        else:
            log.error("amqp_pub_msg_attr should either be None or of type AmqpPublishMessagingAttributes")
            raise TypeError("amqp_pub_msg_attr should either be None or of type AmqpPublishMessagingAttributes")

        self._connect()
        # Declaring edge_system level exchange for publishing metrics
        self.client.declare_publish_exchange(self.pub_msg_attr)

    def _connect(self):
        """
        Initializes AMQP Transport and connects to AMQP broker
        :return:
        """
        self.client = Amqp(self.url, self.port, self.identity, self.tls_conf, self.enable_authentication,
                           self.connection_timeout_sec)

    def _disconnect(self):
        """
        Disconnects from AMQP broker
        :return:
        """
        self.client.disconnect()

    def receive(self, consume_msg_attr_list, auto_gen_callback=None):
        """
        Consumes message for given routing key, ack value and callback.
        :param consume_msg_attr_list: list of AmqpConsumeMessagingAttributes objects or None
        :param auto_gen_callback: callback method to be invoked for auto-generated AmqpConsumeMessagingAttributes
                                  NOTE: AmqpConsumeMessagingAttributes will be outo-generated only when
                                  auto_gen_callback is provided
        :return:
        """
        consume_msg_attr_list = consume_msg_attr_list if consume_msg_attr_list else []

        if not isinstance(consume_msg_attr_list, list):
            log.error("consume_msg_attr_list must be of type list")
            raise TypeError("consume_msg_attr_list must be of type list")

        if auto_gen_callback:
            consume_msg_attr = AmqpConsumeMessagingAttributes(self.edge_system_name, callback=auto_gen_callback)
            consume_msg_attr_list.append(consume_msg_attr)

        self.client.consume(consume_msg_attr_list)

    def send(self, message, pub_msg_attr=None):
        """
        Publishes message to AMQP broker with given routing key
        :param message: Message to be published
        :param pub_msg_attr: AmqpPublishMessagingAttributes Object
        :return:
        """
        if pub_msg_attr:
            # declare exchange if not already declared
            if not pub_msg_attr.is_exchange_declared:
                self.client.declare_publish_exchange(pub_msg_attr)

            if pub_msg_attr.exchange_name is None:
                # Mode 2: Single exchange and different routing-keys for each metric published from an edge_system
                self.client.publish(self.pub_msg_attr.exchange_name, pub_msg_attr.routing_key, message,
                                    pub_msg_attr.properties)
            else:
                # Mode 3: Separate exchange and routing-keys for each metric published from an edge_system
                self.client.publish(pub_msg_attr.exchange_name, pub_msg_attr.routing_key, message,
                                    pub_msg_attr.properties)

        else:
            # Mode 1: Single exchange and routing-key for all metrics published from an edge_system
            self.client.publish(self.pub_msg_attr.exchange_name, self.pub_msg_attr.routing_key, message,
                                self.pub_msg_attr.properties)

    def stop_receiving(self):
        """
        Stops consumer.
        :return:
        """
        self.client.disconnect_consumer()
