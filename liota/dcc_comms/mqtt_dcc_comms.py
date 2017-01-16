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
from liota.lib.transports.mqtt import Mqtt, MqttMessagingAttributes

log = logging.getLogger(__name__)


class MqttDccComms(DCCComms):
    """
    DccComms for MQTT Transport
    """

    def __init__(self, dcc_identity, edge_system_identity, tls_details, qos_details, url, port, client_id=None, clean_session=False,
                 userdata=None, protocol="MQTTv311", transport="tcp", mqtt_msg_attr=None, keep_alive=60,
                 enable_authentication=False, conn_disconn_timeout=10):

        """
        :param dcc_identity: RemoteSystemIdentity object
        :param edge_system_identity: EdgeSystemIdentity object
        :param tls_details: TLSDetails object
        :param qos_details: QoSDetails object
        :param url: MQTT Broker URL or IP
        :param port: MQTT Broker Port
        :param client_id: Client ID
        :param clean_session: Connect with Clean session or not
        :param userdata: userdata is user defined data of any type that is passed as the "userdata"
                         parameter to callbacks.

        :param protocol: allows explicit setting of the MQTT version to use for this client
        :param transport: Set transport to "websockets" to use WebSockets as the transport
                          mechanism. Set to "tcp" to use raw TCP, which is the default.

        :param mqtt_msg_attr: MqttMessagingAttributes object or None
        :param keep_alive: KeepAliveInterval
        :param enable_authentication: Enable user-name password authentication or not
        :param conn_disconn_timeout: Connect-Disconnect-Timeout
        """
        self.dcc_identity = dcc_identity
        self.edge_system_identity = edge_system_identity

        if mqtt_msg_attr is None:
            #  pub-topic and sub-topic will be auto-generated
            self.msg_attr = MqttMessagingAttributes(edge_system_identity.edge_system_name)
        elif isinstance(mqtt_msg_attr, MqttMessagingAttributes):
            self.msg_attr = mqtt_msg_attr
        else:
            log.error("mqtt_mess_attr should either be None or of type MqttMessagingAttributes")
            raise TypeError("mqtt_mess_attr should either be None or of type MqttMessagingAttributes")

        self.tls_details = tls_details
        self.url = url
        self.port = port
        self.client_id = client_id
        self.clean_session = clean_session
        self.userdata = userdata
        self.protocol = protocol
        self.transport = transport
        self.keep_alive = keep_alive
        self.qos_details = qos_details
        self.enable_authentication = enable_authentication
        self.conn_disconn_timeout = conn_disconn_timeout
        self._connect()

    def _connect(self):
        """
        Initializes Mqtt Transport and connects to MQTT broker.
        :return:
        """
        self.client = Mqtt(self.dcc_identity, self.edge_system_identity, self.tls_details, self.qos_details, self.url,
                           self.port, self.client_id, self.clean_session, self.userdata, self.protocol, self.transport,
                           self.keep_alive, self.enable_authentication, self.conn_disconn_timeout)

    def _disconnect(self):
        """
        Disconnects from MQTT broker.
        :return:
        """
        self.client.disconnect()

    def subscribe(self, mess_attr=None):
        """
        Subscribes to a topic with specified QoS and callback.

        :param mess_attr: MqttMessagingAttributes Object
        :return:
        """
        if mess_attr:
            self.client.subscribe(mess_attr.sub_topic, mess_attr.sub_qos, mess_attr.sub_callback)
        else:
            self.client.subscribe(self.msg_attr.sub_topic, self.msg_attr.sub_qos, self.msg_attr.sub_callback)

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

    def receive(self):
        raise NotImplementedError
