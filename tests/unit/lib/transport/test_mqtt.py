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

import unittest
import sys

import mock
from paho.mqtt.client import Client

from liota.lib.transports.mqtt import Mqtt
from liota.lib.transports.mqtt import MqttMessagingAttributes, QoSDetails
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
from liota.lib.utilities.identity import Identity
from liota.lib.utilities.tls_conf import TLSConf
from liota.lib.utilities.utility import systemUUID


# MQTT configurations
config = {}
connect_rc = 0
disconnect_rc = 0


# Monkey patched connect method of Paho client
def mocked_connect(self, *args, **kwargs):
    # Call on_connect method with connection established options connect_rc
    self.on_connect(self._client_id, self._userdata, None, connect_rc)


# Monkey patched disconnect method of Paho client
def mocked_disconnect(self):
    self.on_disconnect(config["client_id"], None, disconnect_rc)


# Monkey patched loop_start method of Paho client
def mocked_loop_start(self, *args, **kwargs):
    pass


# Monkey patched loop_start method of Paho client
def mocked_loop_stop(self, *args, **kwargs):
    pass


# Callback method to use in subscribe function
def topic_subscribe_callback(self, *args, **kwargs):
    pass


class MQTTTest(unittest.TestCase):
    """
    MQTT transport unit test cases
    """

    def setUp(self):
        """
        Method to initialise the MQTT parameters.
        :return: None
        """

        # Broker details
        self.url = "127.0.0.1"
        self.port = 8883
        self.mqtt_username = "test"
        self.mqtt_password = "test"
        self.enable_authentication = True
        self.client_clean_session = True
        self.protocol = "MQTTv311"
        self.transport = "tcp"
        self.connection_disconnect_timeout = 2
        self.user_data = None
        self.client_id = "test-client"
        config["client_id"] = self.client_id

        # Message QoS and connection details
        self.QoSlevel = 2
        self.inflight = 20
        self.queue_size = 0
        self.retry = 5
        self.keep_alive = 60

        # EdgeSystem name
        self.edge_system = Dell5KEdgeSystem("TestEdgeSystem")

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

    def tearDown(self):
        """
        Method to cleanup the resource created during the execution of test case.
        :return: None
        """
        # Broker details
        self.url = None
        self.port = None
        self.mqtt_username = None
        self.mqtt_password = None
        self.enable_authentication = None
        self.client_clean_session = None
        self.protocol = None
        self.transport = None
        self.connection_disconnect_timeout = None
        self.user_data = None
        self.client_id = None
        config["client_id"] = None

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

    @mock.patch.object(Mqtt, 'connect_soc')
    def test_mqtt_init(self, mock_connect):
        """
        Test case to check the implementation of Mqtt class with client clean session flag True.
        :param mock_connect: Mocked connect_soc method
        :return: None
        """

        # Mocked connect_soc method
        mock_connect.returnvalue = None

        mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                           self.client_clean_session, self.user_data, self.protocol, self.transport, self.keep_alive,
                           self.enable_authentication, self.connection_disconnect_timeout)

        # Check we are able to generate Mqtt class object
        self.assertIsInstance(mqtt_client, Mqtt, "Invalid Mqtt class implementation")

    @mock.patch.object(Mqtt, 'connect_soc')
    def test_mqtt_init_clean_session_false(self, mock_connect):
        """
        Test case to test the implementation of Mqtt class for client clean session flag False.
        :param mock_connect: Mocked connect_soc method
        :return: None
        """

        # Mocked connect_soc method
        mock_connect.returnvalue = None

        # Clean session flag as False
        self.client_clean_session = False

        mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                           self.client_clean_session, self.user_data, self.protocol, self.transport, self.keep_alive,
                           self.enable_authentication, self.connection_disconnect_timeout)

        # Check we are able to generate Mqtt class object
        self.assertIsInstance(mqtt_client, Mqtt, "Invalid Mqtt class implementation")

    def test_connect_soc_invalid_root_ca(self):
        """
        Test case to test validation for invalid root ca validation.
        :return: None
        """
        # Setting invalid root ca path
        self.root_ca_cert = "Invalid Root CA Path"

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, self.mqtt_username, self.mqtt_password,
                                 self.client_cert_file, self.client_key_file)

        # Checking whether implementation raising the ValueError for invalid root ca_certs
        with self.assertRaises(ValueError):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_connect_soc_empty_root_ca(self):
        """
        Test case to test validation for empty root ca validation.
        :return: None
        """
        # Setting invalid root ca path
        self.root_ca_cert = ""

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, self.mqtt_username, self.mqtt_password,
                                 self.client_cert_file, self.client_key_file)

        # Checking whether implementation raising the ValueError for invalid root ca_certs
        with self.assertRaises(ValueError):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_connect_soc_invalid_client_ca(self):
        """
        Test case to test validation for invalid client ca validation.
        :return: None
        """
        # Setting invalid client ca path
        self.client_cert_file = "Invalid Client CA Path"

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, self.mqtt_username, self.mqtt_password,
                                 self.client_cert_file, self.client_key_file)

        # Checking whether implementation raising the ValueError for invalid client ca_certs
        with self.assertRaises(ValueError):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_connect_soc_empty_client_ca(self):
        """
        Test case to test validation for empty client certificate.
        :return: None
        """
        # Setting invalid client ca path
        self.client_cert_file = ""

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, self.mqtt_username, self.mqtt_password,
                                 self.client_cert_file, self.client_key_file)

        # Checking whether implementation raising the ValueError for invalid client ca_certs
        with self.assertRaises(ValueError):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_connect_soc_invalid_client_key(self):
        """
        Test case to test the validation for invalid client key.
        :return: None
        """
        # Setting invalid client key path
        self.client_key_file = "Invalid Client Key Path"

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, self.mqtt_username, self.mqtt_password,
                                 self.client_cert_file, self.client_key_file)

        # Checking whether implementation raising the ValueError for invalid client key
        with self.assertRaises(ValueError):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_connect_soc_empty_client_key(self):
        """
        Test case to test validation for empty client key.
        :return: None
        """
        # Setting invalid client cert path
        self.client_key_file = ""

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, self.mqtt_username, self.mqtt_password,
                                 self.client_cert_file, self.client_key_file)

        # Checking whether implementation raising the ValueError for invalid client cert
        with self.assertRaises(ValueError):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_connect_soc_for_empty_username(self):
        """
        Test case to test validation for empty username.
        :return: None
        """

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, "", self.mqtt_password,
                                 self.client_cert_file, self.client_key_file)

        # Checking whether implementation raising the ValueError for invalid username
        with self.assertRaises(ValueError):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_connect_soc_for_empty_password(self):
        """
        Test case to test validation for empty password.
        :return: None
        """

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, self.mqtt_username, "",
                                 self.client_cert_file, self.client_key_file)

        # Checking whether implementation raising the ValueError for empty password
        with self.assertRaises(ValueError):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_connect_soc_connection_setup(self):
        """
        Test case to test connection setup with connect_soc.
        :return: None
        """
        global connect_rc

        # Setting connection accepted flag
        connect_rc = 0

        # Mocked the connect and loop_start method of Paho library
        Client.connect = mocked_connect
        Client.loop_start = mocked_loop_start

        mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                           self.client_clean_session, self.user_data, self.protocol, self.transport,
                           self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

        # Check we are able to generate Mqtt class object
        self.assertIsInstance(mqtt_client, Mqtt, "Invalid Mqtt class implementation")

    def test_connect_soc_connection_timeout(self):
        """
        Test case to test connection setup timeout with connect_soc.
        :return: None
        """
        global connect_rc

        # Setting connection timeout flag
        connect_rc = sys.maxsize

        # Mocked the connect and loop_start method of Paho library
        Client.connect = mocked_connect
        Client.loop_start = mocked_loop_start
        Client.loop_stop = mocked_loop_stop

        # Checking whether implementation raising the Exception for broker timeout
        with self.assertRaises(Exception):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_connect_soc_connection_refused(self):
        """
        Test case to test broker connection refused with connect_soc.
        :return: None
        """
        global connect_rc

        # Setting connection refused flag
        connect_rc = 1

        # Mocked the connect and loop_start method of Paho library
        Client.connect = mocked_connect
        Client.loop_start = mocked_loop_start
        Client.loop_stop = mocked_loop_stop

        # Checking whether implementation raising the Exception for broker connection refused
        with self.assertRaises(Exception):
            Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                 self.client_clean_session, self.user_data, self.protocol, self.transport,
                 self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

    def test_mqtt_connection_over_only_root_ca_cert(self):
        """
        Test case to test the implementation of connection_soc method for root_ca only.
        :return: None
        """
        global connect_rc

        # Encapsulate the authentication details
        self.identity = Identity(self.root_ca_cert, self.mqtt_username, self.mqtt_password, None, None)

        # Setting connection accepted flag
        connect_rc = 0

        # Mocked the connect and loop_start method of Paho library
        Client.connect = mocked_connect
        Client.loop_start = mocked_loop_start

        mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                           self.client_clean_session, self.user_data, self.protocol, self.transport, self.keep_alive,
                           self.enable_authentication, self.connection_disconnect_timeout)
        # Check we are able to generate Mqtt class object
        self.assertIsInstance(mqtt_client, Mqtt, "Invalid Mqtt class implementation")

    @mock.patch.object(Mqtt, 'connect_soc')
    def test_client_clean_session_and_client_id_implementation(self, mock_connect):
        """
        Test case to test the implementation of get_client_id method.
        :param mock_connect: Mocked connect_soc method
        :return: None
        """

        # Mocked connect_soc method
        mock_connect.returnvalue = None

        mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                           self.client_clean_session, self.user_data, self.protocol, self.transport, self.keep_alive,
                           self.enable_authentication, self.connection_disconnect_timeout)

        # Check we are able to generate Mqtt class object
        self.assertIsInstance(mqtt_client, Mqtt, "Invalid Mqtt class implementation")

        client_id = mqtt_client.get_client_id()

        # Checking the client_id implementation
        self.assertEqual(self.client_id, client_id, "Received invalid client-id, check the implementation.")

    def test_clean_disconnect_connection(self):
        """
        Test case to test clean-connection disconnect.
        :return: None
        """
        global connect_rc, disconnect_rc

        # Setting connection accepted flag
        connect_rc = 0
        # Setting connection disconnect flag
        disconnect_rc = 0

        # Monkey patched connect, disconnect, loop_start and loop_stop methods of Paho library
        Client.connect = mocked_connect
        Client.disconnect = mocked_disconnect
        Client.loop_start = mocked_loop_start
        Client.loop_stop = mocked_loop_stop

        mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                           self.client_clean_session, self.user_data, self.protocol, self.transport,
                           self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

        self.assertEqual(mqtt_client.disconnect(), None)

    def test_timeout_disconnect_connection(self):
        """
        Test case to test timeout-connection disconnect.
        :return: None
        """
        global connect_rc, disconnect_rc

        # Setting connection accepted flag
        connect_rc = 0
        # Setting connection disconnect flag
        disconnect_rc = sys.maxsize

        # Monkey patched connect, disconnect, loop_start and loop_stop methods of Paho library
        Client.connect = mocked_connect
        Client.disconnect = mocked_disconnect
        Client.loop_start = mocked_loop_start
        Client.loop_stop = mocked_loop_stop

        # Checking whether implementation raising the Exception for broker disconnect timeout
        with self.assertRaises(Exception):
            mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                               self.client_clean_session, self.user_data, self.protocol, self.transport,
                               self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

            mqtt_client.disconnect()

    def test_invalid_disconnect_connection(self):
        """
        Test case to test invalid-connection disconnect.
        :return: None
        """
        global connect_rc, disconnect_rc

        # Setting connection accepted flag
        connect_rc = 0
        # Setting connection disconnect flag
        disconnect_rc = 2

        # Monkey patched connect, disconnect, loop_start and loop_stop methods of Paho library
        Client.connect = mocked_connect
        Client.disconnect = mocked_disconnect
        Client.loop_start = mocked_loop_start
        Client.loop_stop = mocked_loop_stop

        # Checking whether implementation raising the Exception for broker disconnect
        with self.assertRaises(Exception):
            mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                               self.client_clean_session, self.user_data, self.protocol, self.transport,
                               self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

            mqtt_client.disconnect()

    @mock.patch.object(Mqtt, 'connect_soc')
    @mock.patch.object(Client, 'publish')
    def test_publish(self, mocked_publish, connect_soc):
        """
        Test case to test publish method of Mqtt class.
        :return: None
        """

        mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                           self.client_clean_session, self.user_data, self.protocol, self.transport,
                           self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

        # Publishing the message
        mqtt_client.publish("test/publish", "Testing publish", 1, False)

        # Check underline publish is called with correct arguments
        mocked_publish.assert_called_with("test/publish", "Testing publish", 1, False)

    @mock.patch.object(Mqtt, 'connect_soc')
    @mock.patch.object(Client, 'subscribe')
    @mock.patch.object(Client, "message_callback_add")
    def test_subscribe(self, mocked_callback_add, mocked_subscribe, connect_soc):
        """
        Test case to test the subscribe method.
        :return: None
        """

        mqtt_client = Mqtt(self.url, self.port, self.identity, self.tls_conf, self.qos_details, self.client_id,
                           self.client_clean_session, self.user_data, self.protocol, self.transport,
                           self.keep_alive, self.enable_authentication, self.connection_disconnect_timeout)

        # Subscribing to the topic
        mqtt_client.subscribe("test/subscribe", 1, topic_subscribe_callback)

        # Check underline subscribe is called with correct parameters
        mocked_subscribe.assert_called_with("test/subscribe", 1)

        # Check underline message_callback_add is called with correct parameters
        mocked_callback_add.assert_called_with("test/subscribe", topic_subscribe_callback)


class MqttMessagingAttributesTest(unittest.TestCase):
    def setUp(self):
        """
        Method to initialise the MqttMessagingAttributes class parameters.
        :return: None
        """
        # EdgeSystem name
        self.edge_system = Dell5KEdgeSystem("TestEdgeSystem")

    def tearDown(self):
        """
        Method to cleanup the resource created during the execution of test case.
        :return: None
        """
        self.edge_system = None

    def test_mqtt_messaging_attributes_implementation_for_edge_system_name(self):
        """
        Test case to test the implementation of MqttMessagingAttributes class for automatic topic generation for publish
        and subscribe.
        :return: None
        """

        # Create MqttMessagingAttributes class object
        mqtt_messaging_attribute = MqttMessagingAttributes(self.edge_system.name)

        # Check whether correct topic generated for publish
        self.assertEqual(mqtt_messaging_attribute.pub_topic, 'liota/' + systemUUID().get_uuid(self.edge_system.name)
                         + "/request")

        # Check correct topic generated for subscribe
        self.assertEqual(mqtt_messaging_attribute.sub_topic, 'liota/' +
                         systemUUID().get_uuid(self.edge_system.name) + "/response")

    def test_mqtt_messaging_attributes_implementation_without_edge_system_name(self):
        """
        Test case to test the implementation of MqttMessagingAttributes class for provided sub/pub topics.
        :return: None
        """

        # Create MqttMessagingAttributes class object
        mqtt_messaging_attribute = MqttMessagingAttributes(pub_topic="test/pub/topic", sub_topic="test/sub/topic")

        # Check whether provided topic used for publish
        self.assertEqual(mqtt_messaging_attribute.pub_topic, "test/pub/topic")

        # Check whether provided topic used for subscribe
        self.assertEqual(mqtt_messaging_attribute.sub_topic, "test/sub/topic")

    def test_validation_of_sub_qos_mqtt_messaging_attributes(self):
        """
        Test case to test validation of MqttMessagingAttributes class subscribe qos levels.
        :return: None
        """
        self.assertRaises(ValueError, MqttMessagingAttributes, self.edge_system.name, None, None, 1, -1)

    def test_validation_of_pub_qos_mqtt_messaging_attributes(self):
        """
        Test case to test validation of MqttMessagingAttributes class publish qos levels.
        :return: None
        """
        self.assertRaises(ValueError, MqttMessagingAttributes, self.edge_system.name, None, None, -1, 1)

    def test_validation_of_retain_flag_mqtt_messaging_attributes(self):
        """
        Test case to test validation of MqttMessagingAttributes class retain flag.
        :return: None
        """
        self.assertRaises(ValueError, MqttMessagingAttributes, self.edge_system.name, None, None, pub_retain="")

    def test_validation_of_sub_callback_mqtt_messaging_attributes(self):
        """
        Test case to test validation of MqttMessagingAttributes sub_callback argument.
        :return: None
        """
        self.assertRaises(ValueError, MqttMessagingAttributes, self.edge_system.name,
                          sub_callback="")

    def test_validation_of_sub_and_pub_topic_attributes(self):
        """
        Test case to test validation of subscribe, publish and sub_callback attributes.
        :return: None
        """
        self.assertRaises(ValueError, MqttMessagingAttributes)


class QoSDetailsTest(unittest.TestCase):
    def setUp(self):
        """
        Method to initialise the QoSDetails class parameters.
        :return: None
        """
        # QoS details
        self.retry = 5
        self.inflight = 20
        self.queue_size = 0

    def tearDown(self):
        """
        Method to cleanup the resource created during the execution of test case.
        :return: None
        """
        # QoS details
        self.retry = None
        self.inflight = None
        self.queue_size = None

    def test_QoS_class_implementation(self):
        """
        Test case to test the implementation of QoSDetails class.
        :return: None
        """
        qos_details = QoSDetails(self.inflight, self.queue_size, self.retry)

        # Check value of retry
        self.assertEqual(qos_details.retry, self.retry, "Invalid implementation for QoSDetails class")

        # Check value of inflight
        self.assertEqual(qos_details.in_flight, self.inflight, "Invalid implementation for QoSDetails class")

        # Check value of queue_size
        self.assertEqual(qos_details.queue_size, self.queue_size, "Invalid implementation for QoSDetails class")


if __name__ == '__main__':
    unittest.main(verbosity=1)
