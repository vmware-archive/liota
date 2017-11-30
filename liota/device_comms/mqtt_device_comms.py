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

from liota.device_comms.device_comms import DeviceComms
from liota.lib.transports.mqtt import Mqtt

log = logging.getLogger(__name__)


class MqttDeviceComms(DeviceComms):
    """
    DeviceComms for MQTT Transport
    """

    def __init__(self, url, port, identity=None, tls_conf=None, qos_details=None,
                 client_id="", clean_session=False, userdata=None, protocol="MQTTv311", transport="tcp", keep_alive=60,
                 enable_authentication=False, conn_disconn_timeout=10):
        """
        :param url: MQTT Broker URL or IP
        :param port: MQTT Broker Port
        :param identity: Identity object
        :param tls_conf: TLSConf object
        :param qos_details: QoSDetails object
        :param client_id: Client ID
        :param clean_session: Connect with Clean session or not
        :param userdata: userdata is user defined data of any type that is passed as the "userdata"
                         parameter to callbacks.

        :param protocol: allows explicit setting of the MQTT version to use for this client
        :param transport: Set transport to "websockets" to use WebSockets as the transport
                          mechanism. Set to "tcp" to use raw TCP, which is the default.

        :param keep_alive: KeepAliveInterval
        :param enable_authentication: Enable user-name password authentication or not
        :param conn_disconn_timeout: Connect-Disconnect-Timeout
        """
        self.url = url
        self.port = port
        self.identity = identity
        self.tls_conf = tls_conf
        self.client_id = client_id
        self.qos_details = qos_details
        self.clean_session = clean_session
        self.userdata = userdata
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

    def publish(self, topic, message, qos, retain=False):
        """
        Publishes message to the MQTT Broker

        :param topic: Publish topic
        :param message: Message to be published
        :param qos: Publish QoS
        :param retain: Message to be retained or not
        :return:
        """
        self.client.publish(topic, message, qos, retain)

    def subscribe(self, topic, qos, callback):
        """
        Subscribes to a topic with given callback

        :param topic: Subscribe topic
        :param qos: Subscribe QoS
        :param callback:  Callback for the topic
        :return:
        """
        self.client.subscribe(topic, qos, callback)

    def send(self, message):
        """
        Send message to MQTT broker.
        TODO: To be implemented.
        Use publish directly.
        :param message: String message to be sent.
        :return:
        """
        raise NotImplementedError

    def receive(self):
        """
        Receive message from MQTT broker.
        TODO: To be implemented.
        USe subscribe directly.
        :return:
        """
        raise NotImplementedError
