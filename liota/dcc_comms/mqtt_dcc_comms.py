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
import Queue

from liota.dcc_comms.dcc_comms import DCCComms
from liota.lib.transports.mqtt import Mqtt, MqttMessagingAttributes
from liota.lib.utilities.utility import systemUUID

log = logging.getLogger(__name__)


class MqttDccComms(DCCComms):
    """
    DccComms for MQTT Transport
    """

    def __init__(self, edge_system_name, url, port, identity=None, tls_conf=None, qos_details=None,
                 client_id=None, clean_session=False, protocol="MQTTv311", transport="tcp", keep_alive=60,
                 mqtt_msg_attr=None, enable_authentication=False, conn_disconn_timeout=10):

        """
        :param edge_system_name: EdgeSystem's name for auto-generation of topic
        :param url: MQTT Broker URL or IP
        :param port: MQTT Broker Port
        :param tls_conf: TLSConf object
        :param identity: Identity object
        :param qos_details: QoSDetails object
        :param client_id: Client ID
        :param clean_session: Connect with Clean session or not
        :param userdata: userdata is user defined data of any type that is passed as the "userdata"
                         parameter to callbacks.

        :param protocol: allows explicit setting of the MQTT version to use for this client
        :param transport: Set transport to "websockets" to use WebSockets as the transport
                          mechanism. Set to "tcp" to use raw TCP, which is the default.

        :param keep_alive: KeepAliveInterval
        :param mqtt_msg_attr: MqttMessagingAttributes object or None.
                            In case of None, topics will be auto-generated. User provided topic will be used otherwise.
        :param enable_authentication: Enable user-name password authentication or not
        :param conn_disconn_timeout: Connect-Disconnect-Timeout
        """

        self.client_id = client_id

        if self.client_id is None:
            #  local_uuid generated will be the client ID
            self.client_id = systemUUID().get_uuid(edge_system_name)
            log.debug("Auto-Generated local uuid will be the client ID {0}".format(self.client_id))
        else:
            log.debug("Client ID is provided by user {0}".format(self.client_id))

        if mqtt_msg_attr is None:
            #  pub-topic and sub-topic will be auto-generated
            log.debug("Pub-topic and Sub-topic are auto-generated")
            self.msg_attr = MqttMessagingAttributes(edge_system_name)
        elif isinstance(mqtt_msg_attr, MqttMessagingAttributes):
            log.debug("User configured pub-topic and sub-topic")
            self.msg_attr = mqtt_msg_attr
        else:
            log.error("mqtt_mess_attr should either be None or of type MqttMessagingAttributes")
            raise TypeError("mqtt_mess_attr should either be None or of type MqttMessagingAttributes")

        self.url = url
        self.port = port
        self.identity = identity
        self.tls_conf = tls_conf
        self.qos_details = qos_details
        self.clean_session = clean_session
        self.userdata = Queue.Queue()
        self.protocol = protocol
        self.transport = transport
        self.keep_alive = keep_alive
        self.enable_authentication = enable_authentication
        self.conn_disconn_timeout = conn_disconn_timeout
        self._connect()

    def _connect(self):
        """
        Initializes Mqtt Transport and connects to MQTT broker.
        :return:
        """
        self.client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                           self.clean_session, self.userdata, self.protocol, self.transport, self.keep_alive,
                           self.enable_authentication, self.conn_disconn_timeout)

    def _disconnect(self):
        """
        Disconnects from MQTT broker.
        :return:
        """
        self.client.disconnect()

    def receive(self, msg_attr=None):
        """
        Subscribes to a topic with specified QoS and callback.
        Set call back to receive_message method if no callback method is passed by user.

        :param msg_attr: MqttMessagingAttributes Object
        :return:
        """
        callback = msg_attr.sub_callback if msg_attr and msg_attr.sub_callback else self.receive_message
        if msg_attr:
            self.client.subscribe(msg_attr.sub_topic, msg_attr.sub_qos, callback)
        else:
            self.client.subscribe(self.msg_attr.sub_topic, self.msg_attr.sub_qos, callback)

    def receive_message(self, client, userdata, msg):
        """
           Receives message during MQTT subscription and put it in the queue.
           This queue can be used to get message in DCC but remember to dequeue

           :param msg_attr: MqttMessagingAttributes Object, userdata as queue
           :return:
           """
        userdata.put(str(msg.payload))

    def send(self, message, msg_attr=None):
        """
        Publishes message to MQTT broker.
        If mess_attr is None, then self.mess_attr will be used.

        :param message: Message to be published
        :param msg_attr: MqttMessagingAttributes Object
        :return:
        """
        if msg_attr:
            self.client.publish(msg_attr.pub_topic, message, msg_attr.pub_qos, msg_attr.pub_retain)
        else:
            self.client.publish(self.msg_attr.pub_topic, message, self.msg_attr.pub_qos,
                                self.msg_attr.pub_retain)
