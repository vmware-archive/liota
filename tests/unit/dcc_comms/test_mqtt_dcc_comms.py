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

import Queue
import logging
import os
import unittest
from ConfigParser import ConfigParser

import mock
import paho.mqtt.client as paho

from liota.dcc_comms.mqtt_dcc_comms import MqttDccComms
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
from liota.lib.transports.mqtt import Mqtt, MqttMessagingAttributes, QoSDetails
from liota.lib.utilities.identity import Identity
from liota.lib.utilities.tls_conf import TLSConf
from liota.lib.utilities.utility import read_liota_config
from liota.lib.utilities.utility import systemUUID

log = logging.getLogger(__name__)


# Callback function for subscribe and publish
def callback_function(*args, **kwargs):
    pass


class MqttDccCommsTest(unittest.TestCase):
    """
    Unit test cases for MQTT DccComms
    """

    @mock.patch.object(Mqtt, 'connect_soc')
    def setUp(self, mock_connect):
        """
        Setup all required parameters for MQTT DCC communication tests
        :param mock_connect: Mocked MQTT connect method
        :return: None
        """
        # ConfigParser to parse ini file
        self.config = ConfigParser()
        self.uuid_file = read_liota_config('UUID_PATH', 'uuid_path')

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
        self.client_id = "test-client"

        # Message QoS and connection details
        self.QoSlevel = 2
        self.inflight = 20
        self.queue_size = 0
        self.retry = 5
        self.keep_alive = 60

        # EdgeSystem name
        self.edge_system = Dell5KEdgeSystem("TestGateway")

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

        # Creating messaging attributes
        self.mqtt_msg_attr = MqttMessagingAttributes(pub_topic="publish-topic", sub_topic="subscribe-topic",
                                                     pub_retain=False, sub_callback=callback_function)

        # Instantiate client for DCC communication
        self.client = MqttDccComms(edge_system_name=self.edge_system.name,
                                   url=self.url, port=self.port, clean_session=self.clean_session,
                                   mqtt_msg_attr=self.mqtt_msg_attr)

    def tearDown(self):
        """
        Clean up all parameters used in test cases
        :return: None
        """

        # Check path exists
        if os.path.exists(self.uuid_file):
            try:
                # Remove the file
                os.remove(self.uuid_file)
            except OSError as e:
                log.error("Unable to remove UUID file" + str(e))

        self.config = None
        self.uuid_file = None
        self.edge_system = None
        self.url = None
        self.port = None
        self.mqtt_username = None
        self.mqtt_password = None
        self.enable_authentication = None
        self.clean_session = None
        self.protocol = None
        self.transport = None
        self.connection_disconnect_timeout = None
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

    @mock.patch.object(Mqtt, 'connect_soc')
    def test_init_no_msgattr_no_client_id(self, mock_connect):
        """
        Test MqttDccComms initialisation without messaging attributes and no client ID
        :param mock_connect: Mocked MQTT connect method
        :return: None
        """

        # Instantiate client for DCC communication
        MqttDccComms(edge_system_name=self.edge_system.name, url=self.url, port=self.port, mqtt_msg_attr=None,
                     client_id="", clean_session=self.clean_session)

        # Read uuid.ini
        self.config.read(self.uuid_file)

        edge_system_name = self.config.get('GATEWAY', 'name')
        local_uuid = self.config.get('GATEWAY', 'local-uuid')

        # Compare stored edge system name
        self.assertEquals(edge_system_name, self.edge_system.name)

        # Compare stored client-id
        self.assertEquals(local_uuid, systemUUID().get_uuid(self.edge_system.name))

        # Check _connect method call has been made
        mock_connect.assert_called()

    @mock.patch.object(Mqtt, 'connect_soc')
    def test_init_no_msgattr_with_client_id(self, mock_connect):
        """
        Test MqttDccComms initialisation without messaging attributes and non-empty client ID
        :param mock_connect: Mocked MQTT connect method
        :return: None
        """
        MqttDccComms(edge_system_name=self.edge_system.name, url=self.url, port=self.port, mqtt_msg_attr=None,
                     client_id=self.client_id, clean_session=self.clean_session)

        # Read uuid.ini
        self.config.read(self.uuid_file)

        edge_system_name = self.config.get('GATEWAY', 'name')
        local_uuid = self.config.get('GATEWAY', 'local-uuid')

        # Validate stored edge system name
        self.assertEquals(edge_system_name, self.edge_system.name)

        # Validate stored client-id
        self.assertEquals(local_uuid, self.client_id)

        # Check _connect method call has been made
        mock_connect.assert_called()

    @mock.patch.object(Mqtt, 'connect_soc')
    def test_init_with_valid_msgattr_with_client_id(self, mock_connect):
        """
        Test MqttDccComms initialisation with valid messaging attributes and non-empty client id
        :param mock_connect: Mocked MQTT connect method
        :return: None
        """

        # Test with valid messaging attributes
        client = MqttDccComms(edge_system_name=self.edge_system.name, url=self.url, port=self.port,
                              client_id=self.client_id, clean_session=self.clean_session,
                              mqtt_msg_attr=self.mqtt_msg_attr)

        # Validate client id
        self.assertEquals(client.client_id, self.client_id)

        # Check connect_soc call has been made
        mock_connect.assert_called()

    @mock.patch.object(Mqtt, 'connect_soc')
    def test_init_with_valid_msg_attr_empty_client_id(self, mock_connect):
        """
        Test MqttDccComms initialisation with valid messaging attributes with empty client id to check implementation 
        creating the ini file. 
        :param mock_connect: Mocked MQTT connect method
        :return: None
        """

        # Test with valid messaging attributes
        mqtt_dcc_client = MqttDccComms(edge_system_name=self.edge_system.name,
                                       url=self.url, port=self.port, client_id="", clean_session=self.clean_session,
                                       mqtt_msg_attr=self.mqtt_msg_attr)

        # Check uuid file get created or not
        self.assertFalse(os.path.exists(self.uuid_file))

        # Validate the client id
        self.assertEqual(mqtt_dcc_client.client_id, "")

        # Check connect_soc call has been made
        mock_connect.assert_called()

    def test_init_with_invalid_msg_attr(self):
        """
        Test initialisation with invalid messaging attributes
        :return: None
        """
        # Pass invalid mqtt messaging attribute
        self.assertRaises(TypeError, lambda: MqttDccComms(edge_system_name=self.edge_system.name, url=self.url,
                                                          port=self.port, clean_session=self.clean_session,
                                                          mqtt_msg_attr=""))

    @mock.patch.object(Mqtt, '__init__')
    def test_connect(self, mock_init):
        """
        Test MqttDccComms _connect method.
        :param mock_init: Mocked MQTT init method
        :return: None
        """
        mock_init.return_value = None

        # Create MqttDCCComms object
        mqtt_dcc_comms = MqttDccComms(edge_system_name=self.edge_system.name, url=self.url, port=self.port,
                                      identity=self.identity, tls_conf=self.tls_conf, qos_details=self.qos_details,
                                      client_id=self.client_id, clean_session=self.clean_session,
                                      protocol=self.protocol, transport=self.transport, keep_alive=self.keep_alive,
                                      mqtt_msg_attr=self.mqtt_msg_attr,
                                      enable_authentication=self.enable_authentication,
                                      conn_disconn_timeout=self.connection_disconnect_timeout)

        # Validate Mqtt __init__ called with following parameters
        mock_init.assert_called_with(self.url, self.port, self.identity, self.tls_conf,
                                     self.qos_details, self.client_id, self.clean_session, mqtt_dcc_comms.userdata,
                                     self.protocol, self.transport, self.keep_alive, self.enable_authentication,
                                     self.connection_disconnect_timeout)

    @mock.patch.object(Mqtt, 'disconnect')
    def test_disconnect(self, mock_disconnect):
        """
        Test MqttDccComms _disconnect method
        :param mock_disconnect: Mocked MQTT disconnect method
        :return: None
        """
        # Call MqttDccComms _disconnect
        self.client._disconnect()

        # Check call made to the Mqtt disconnect method
        mock_disconnect.assert_called()

    @mock.patch.object(Mqtt, 'publish')
    def test_send_with_msg_attr(self, mock_publish):
        """
        Test MqttDccComms send method with messaging attributes
        :param mock_publish: Mocked MQTT publish method
        :return: None
        """

        # Create publish MqttMessagingAttributes
        mqtt_msg_attr = MqttMessagingAttributes(pub_topic="test/publish_topic", pub_qos=2, pub_retain=True)

        # Call MqttDccComms send method
        self.client.send(message=self.publish_message, msg_attr=mqtt_msg_attr)

        # Check implementation calling Mqtt publish method with following params
        mock_publish.assert_called_with(mqtt_msg_attr.pub_topic, self.publish_message,
                                        mqtt_msg_attr.pub_qos, mqtt_msg_attr.pub_retain)

    @mock.patch.object(Mqtt, 'publish')
    def test_send_without_msg_attr(self, mock_publish):
        """
        Test MqttDccComms send method without messaging attributes
        :param mock_publish: Mocked MQTT publish method
        :return: None
        """
        # Call MqttDccComms send method
        self.client.send(message=self.publish_message, msg_attr=None)

        # Check implementation calling Mqtt publish method with following params
        mock_publish.assert_called_with(self.client.msg_attr.pub_topic, self.publish_message,
                                        self.client.msg_attr.pub_qos, self.client.msg_attr.pub_retain)

    @mock.patch.object(Mqtt, 'subscribe')
    def test_receive(self, mocked_subscribe):
        """
        Test MqttDccComms receive method implementation with msg_attr.
        :return: None 
        """
        # Create subscribe MqttMessagingAttributes messaging attribute
        mqtt_msg_attr = MqttMessagingAttributes(self.edge_system.name, sub_topic="test/subscribe_topic", sub_qos=2,
                                                sub_callback=callback_function)

        # Call receive with mqtt_msg_attr
        self.client.receive(mqtt_msg_attr)

        # Check underline subscribe called with following parameters
        mocked_subscribe.assert_called_with(mqtt_msg_attr.sub_topic, mqtt_msg_attr.sub_qos,
                                            mqtt_msg_attr.sub_callback)

    @mock.patch.object(Mqtt, 'subscribe')
    def test_receive_without_msg_attr(self, mocked_subscribe):
        """
        Test MqttDccComms receive method implementation without msg_attr.
        :return: None 
        """

        # Call receive without mqtt_msg_attr
        self.client.receive()

        # Check underline subscribe called with following parameters
        mocked_subscribe.assert_called_with(self.mqtt_msg_attr.sub_topic, self.mqtt_msg_attr.sub_qos,
                                            self.client.receive_message)

    @mock.patch.object(Mqtt, 'subscribe')
    @mock.patch.object(Mqtt, '__init__')
    def test_receive_with_msg_attr(self, init, mocked_subscribe):
        """
        Test MqttDccComms receive method implementation with msg_attr.
        :return: None 
        """
        # Assign mocked method return value
        init.return_value = None

        # Instantiate client for DCC communication
        self.client = MqttDccComms(edge_system_name=self.edge_system.name, url=self.url, port=self.port,
                                   mqtt_msg_attr=None, client_id="", clean_session=self.clean_session)

        # Call receive with mqtt_msg_attr
        self.client.receive(self.mqtt_msg_attr)

        # Check underline subscribe called with following parameters
        mocked_subscribe.assert_called_with(self.mqtt_msg_attr.sub_topic, self.mqtt_msg_attr.sub_qos,
                                            self.mqtt_msg_attr.sub_callback)

    @mock.patch.object(Queue.Queue, "put")
    def test_receive_message(self, mocked_put):
        """
        Test MqttDccComms receive_message method implementation.
        :return: None 
        """
        # Creating the MQTTMessage
        message = paho.MQTTMessage(topic="test/subscribe")

        # Create sample payload data
        message.payload = "test-payload"

        # Call receive_message method
        self.client.receive_message(self.client_id, self.client.userdata, msg=message)

        # Check put method called with following parameters
        mocked_put.assert_called_with(message.payload)


if __name__ == '__main__':
    unittest.main(verbosity=1)
