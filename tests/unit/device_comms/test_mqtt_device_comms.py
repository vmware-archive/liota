# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2015-2017 VMware, Inc. All Rights Reserved.                    #
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

import unittest

import mock

from liota.device_comms.mqtt_device_comms import MqttDeviceComms
from liota.lib.transports.mqtt import Mqtt, QoSDetails
from liota.lib.utilities.identity import Identity
from liota.lib.utilities.tls_conf import TLSConf


# Callback function for subscribe and publish
def callback_function():
    pass


class MqttDeviceCommsTest(unittest.TestCase):
    """
    Unit test cases for MQTT DeviceComms
    """

    @mock.patch.object(Mqtt, 'connect_soc')
    def setUp(self, mock_connect):
        """
        Setup all required parameters for MQTT device communication tests
        :param mock_connect: Mocked MQTT connect method
        :return:
        """

        # Broker details
        self.url = "Broker-IP"
        self.port = "Broker-Port"
        self.mqtt_username = "test"
        self.mqtt_password = "test"
        self.enable_authentication = True
        self.clean_session = True
        self.protocol = "MQTTv311"
        self.transport = "tcp"
        self.connection_disconnect_timeout = 2
        self.user_data = None
        self.client_id = "test-client"

        # Message QoS and connection details
        self.QoSlevel = 2
        self.inflight = 20
        self.queue_size = 0
        self.retry = 5
        self.keep_alive = 60

        # TLS configurations
        self.root_ca_cert = "/etc/liota/mqtt/conf/ca.crt"
        self.client_cert_file = "/etc/liota/mqtt/conf/client.crt"
        self.client_key_file = "/etc/liota/mqtt/conf/client.key"
        self.cert_required = "CERT_REQUIRED"
        self.tls_version = "PROTOCOL_TLSv1"
        self.cipher = None

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, self.mqtt_username, self.mqtt_password,
                                 self.client_cert_file, self.client_key_file)

        # Encapsulate TLS parameters
        self.tls_conf = TLSConf(self.cert_required, self.tls_version, self.cipher)

        # Encapsulate QoS related parameters
        self.qos_details = QoSDetails(self.inflight, self.queue_size, self.retry)

        self.publish_message = "test-message"
        self.publish_topic = "publish-topic"
        self.subscribe_topic = "subscribe-topic"
        self.publish_message = "test-message"

        # Instantiate client for DCC communication
        self.client = MqttDeviceComms(url=self.url, port=self.port, clean_session=self.clean_session)

    def tearDown(self):
        """
        Clean up all parameters used in test cases
        :return:
        """
        self.url = None
        self.port = None
        self.mqtt_username = None
        self.mqtt_password = None
        self.enable_authentication = None
        self.clean_session = None
        self.protocol = None
        self.transport = None
        self.connection_disconnect_timeout = None
        self.user_data = None
        self.client_id = None

        # Message QoS and connection details
        self.QoSlevel = None
        self.inflight = None
        self.queue_size = None
        self.retry = None
        self.keep_alive = None

        # EdgeSystem name
        self.edge_system = None

        # TLS configurations
        self.root_ca_cert = None
        self.client_cert_file = None
        self.client_key_file = None
        self.cert_required = None
        self.tls_version = None
        self.cipher = None

        # Identity
        self.identity = None

        # TLS configurations
        self.tls_conf = None

        # QoS configurations
        self.qos_details = None

        self.publish_message = None
        self.mqtt_msg_attr = None
        self.client = None

        self.publish_topic = None
        self.subscribe_topic = None
        self.publish_message = None
        self.client = None

    @mock.patch.object(Mqtt, 'connect_soc')
    def test_init(self, mock_connect):
        """
        Test MqttDeviceComms initialisation.
        :param mock_connect: Mocked MQTT connect method
        :return: None
        """
        # Create MqttDeviceComms class object
        MqttDeviceComms(url=self.url, port=self.port, clean_session=self.clean_session)

        # Check implementation calling _connect method
        mock_connect.assert_called()

    @mock.patch.object(Mqtt, '__init__')
    def test_connect(self, mock_init):
        """
        Test MqttDeviceComms _connect method implementation.
        :param mock_init: Mocked MQTT init method
        :return:
        """
        mock_init.return_value = None

        # Create MqttDeviceComms class object
        MqttDeviceComms(url=self.url, port=self.port, identity=self.identity, tls_conf=self.tls_conf,
                        qos_details=self.qos_details, client_id=self.client_id,
                        clean_session=self.clean_session, userdata=self.user_data, protocol=self.protocol,
                        transport=self.transport, keep_alive=self.keep_alive,
                        enable_authentication=self.enable_authentication,
                        conn_disconn_timeout=self.connection_disconnect_timeout)

        # Check Mqtt __init__ called with following params
        mock_init.assert_called_with(self.url, self.port, self.identity, self.tls_conf, self.qos_details,
                                     self.client_id, self.clean_session, self.user_data, self.protocol,
                                     self.transport, self.keep_alive, self.enable_authentication,
                                     self.connection_disconnect_timeout)

    @mock.patch.object(Mqtt, 'disconnect')
    def test_disconnect(self, mock_disconnect):
        """
        Test MqttDeviceComms _disconnect method.
        :param mock_disconnect: Mocked MQTT disconnect method
        :return: None
        """
        # Call MqttDeviceComms _disconnect method
        self.client._disconnect()

        # Check implementation calling Mqtt disconnect
        mock_disconnect.assert_called()

    @mock.patch.object(Mqtt, 'publish')
    def test_publish(self, mock_publish):
        """
        Test MqttDeviceComms publish method implementation.
        :param mock_publish: Mocked MQTT publish method
        :return: None
        """
        # Call MqttDeviceComms publish method
        self.client.publish(topic=self.publish_topic, message=self.publish_message, qos=1, retain=False)

        # Check implementation calling the Mqtt publish method with following params
        mock_publish.assert_called_with(self.publish_topic, self.publish_message, 1, False)

    @mock.patch.object(Mqtt, 'subscribe')
    def test_subscribe(self, mock_subscribe):
        """
        Tests MqttDeviceComms subscribe method implementation.
        :param mock_subscribe: Mocked MQTT subscribe method
        :return: None
        """
        # Call MqttDeviceComms subscribe method
        self.client.subscribe(topic=self.subscribe_topic, qos=1, callback=callback_function)

        # Check implementation calling the Mqtt subscribe with following params
        mock_subscribe.assert_called_with(self.subscribe_topic, 1, callback_function)

    def test_send(self):
        """
        Tests MqttDeviceComms send method implementation.
        :return: None 
        """

        # Check implementation raising the NotImplementedError exception or not
        self.assertRaises(NotImplementedError, lambda: self.client.send(self.publish_message))

    def test_receive(self):
        """
        Tests MqttDeviceComms receive method implementation.
        :return: None 
        """

        # Check implementation raising the NotImplementedError exception or not
        self.assertRaises(NotImplementedError, lambda: self.client.receive())


if __name__ == '__main__':
    unittest.main(verbosity=1)
