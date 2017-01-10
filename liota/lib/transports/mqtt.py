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
import sys
import time

import paho.mqtt.client as paho

from liota.lib.utilities.utility import systemUUID


log = logging.getLogger(__name__)


class Mqtt():
    """
    MQTT Transport implementation for LIOTA. It internally uses Python Paho library.
    """

    def on_connect(self, client, userdata, flags, rc):
        """
        Invoked on successful connection to a broker after connection request

        :param client: The client instance for this callback
        :param userdata: The private user data as set in Client() or userdata_set()
        :param flags: Response flags sent by the broker
        :param rc: The connection result
        :return:
        """
        self._connect_result_code = rc
        self._disconnect_result_code = sys.maxsize
        log.info("Connected with result code : {0} : {1} ".format(str(rc), paho.connack_string(rc)))

    def on_disconnect(self, client, userdata, rc):
        """
        Invoked when disconnected from broker.  Two scenarios are possible:

        1) Broker rejects a connection request
        2) Client initiated disconnect

        :param client: The client instance for this callback
        :param userdata: The private user data as set in Client() or userdata_set()
        :param rc: The connection result
        :return:
        """
        self._connect_result_code = sys.maxsize
        self._disconnect_result_code = rc
        log.info("Disconnected with result code : {0} : {1} ".format(str(rc), paho.connack_string(rc)))

    def on_message(self, client, userdata, msg):
        """
        Invoked when message received on a subscribed topic.

        :param client: The client instance for this callback
        :param userdata: The private user data as set in Client() or userdata_set()
        :param msg: An instance of MQTTMessage. This is a class with members topic, payload, qos, retain.
        :return:
        """
        log.debug("On Message {0} {1} {2}".format(msg.topic, str(msg.qos), str(msg.payload)))

    def on_publish(self, client, userdata, mid):
        """
        Called when publish transmission is completed.

        :param client: The client instance for this callback
        :param userdata: The private user data as set in Client() or userdata_set()
        :param mid: Message ID
        :return:
        """
        log.debug("mid: {0}".format(str(mid)))

    def on_subscribe(self, client, userdata, mid, granted_qos):
        """
        Invoked when the broker responds to subscribe request.

        :param client: The client instance for this callback
        :param userdata: The private user data as set in Client() or userdata_set()
        :param mid: Message ID
        :param granted_qos: Greanted QoS by the broker
        :return:
        """
        log.debug("Subscribed: {0} {1}".format(str(mid), str(granted_qos)))

    def on_unsubscribe(self, client, userdata, mid):
        """
        Invoked when the broker responds to an unsubscribe request.

        :param client: The client instance for this callback
        :param userdata: The private user data as set in Client() or userdata_set()
        :param mid: Message ID
        :return:
        """
        log.debug("Unsubscribed: {0}".format(str(mid)))

    def __init__(self, remote_system_identity, edge_system_identity, tls_details, qos_details, url, port, client_id="", clean_session=False,
                 userdata=None, protocol="MQTTv311", transport="tcp", keep_alive=60, enable_authentication=False,
                 conn_disconn_timeout=10):

        """
        :param remote_system_identity: remote_system_identity object
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

        :param keep_alive: KeepAliveInterval
        :param enable_authentication: Enable user-name password authentication or not
        :param conn_disconn_timeout: Connect-Disconnect-Timeout
        """
        self.remote_system_identity = remote_system_identity
        self.edge_system_identity = edge_system_identity
        self.tls_details = tls_details
        self.url = url
        self.port = port
        self.keep_alive = keep_alive
        self.qos_details = qos_details
        self.enable_authentication = enable_authentication
        self._conn_disconn_timeout = conn_disconn_timeout
        if clean_session:
            # If user passes client_id, it'll be used.  Otherwise, it is left to the underlying paho
            # to generate random client_id
            self._paho_client = paho.Client(client_id, clean_session=True, userdata=userdata,
                                            protocol=getattr(paho, protocol), transport=transport)
        else:
            #  client_id given by user
            if client_id is not None and (client_id != ""):
                self._paho_client = paho.Client(client_id, clean_session=False)
            else:
                #  local-uuid of the gateway will be the client name
                self._paho_client = paho.Client(client_id=systemUUID().get_uuid(edge_system_identity.edge_system_name),
                                                clean_session=False, userdata=userdata,
                                                protocol=getattr(paho, protocol), transport=transport)
        self._connect_result_code = sys.maxsize
        self._disconnect_result_code = sys.maxsize
        self._paho_client.on_message = self.on_message
        self._paho_client.on_publish = self.on_publish
        self._paho_client.on_subscribe = self.on_subscribe
        self._paho_client.on_connect = self.on_connect
        self._paho_client.on_disconnect = self.on_disconnect
        self.connect_soc()

    def connect_soc(self):
        """
        Establishes connection with MQTT Broker
        :return:
        """
        # Set up TLS support
        if self.tls_details:

            # Validate CA certificate path
            if self.remote_system_identity.root_ca_cert:
                if not(os.path.exists(self.remote_system_identity.root_ca_cert)):
                    log.error("Error : Wrong CA certificate path.")
                    raise ValueError("Error : Wrong CA certificate path.")
            else:
                log.error("Error : Wrong CA certificate path.")
                raise ValueError("Error : CA certificate path is missing")

            # Validate client certificate path
            if self.edge_system_identity.cert_file:
                if os.path.exists(self.edge_system_identity.cert_file):
                    client_cert_available = True
                else:
                    log.error("Error : Wrong client certificate path.")
                    raise ValueError("Error : Wrong client certificate path.")
            else:
                client_cert_available = False

            # Validate client key file path
            if self.edge_system_identity.key_file:
                if os.path.exists(self.edge_system_identity.key_file):
                    client_key_available = True
                else:
                    log.error("Error : Wrong client key path.")
                    raise ValueError("Error : Wrong client key path.")
            else:
                client_key_available = False

            '''
                Multiple conditions for certificate validations
                # 1. Both Client certificate and key file should be present
                # 2. If both are not there proceed without client certificate and key
                # 3. If client certificate is not there throw an error
                # 4. If client key is not there throw an error
            '''

            if client_cert_available and client_key_available:
                log.debug("Certificates : ", self.remote_system_identity.root_ca_cert, self.edge_system_identity.cert_file,
                          self.edge_system_identity.key_file)

                self._paho_client.tls_set(self.remote_system_identity.root_ca_cert, self.edge_system_identity.cert_file,
                                          self.edge_system_identity.key_file,
                                          cert_reqs=getattr(ssl, self.tls_details.cert_required),
                                          tls_version=getattr(ssl, self.tls_details.tls_version),
                                          ciphers=self.tls_details.cipher)
            elif not client_cert_available and not client_key_available:
                self._paho_client.tls_set(self.remote_system_identity.root_ca_cert,
                                          cert_reqs=getattr(ssl, self.tls_details.cert_required),
                                          tls_version=getattr(ssl, self.tls_details.tls_version),
                                          ciphers=self.tls_details.cipher)
            elif not client_cert_available and client_key_available:
                log.error("Error : Client key found, but client certificate not found")
                raise ValueError("Error : Client key found, but client certificate not found")
            else:
                log.error("Error : Client key found, but client certificate not found")
                raise ValueError("Error : Client certificate found, but client key not found")
            log.info("TLS support is set up.")

        # Set up username-password
        if self.enable_authentication:
            if not self.remote_system_identity.username:
                log.error("Username not found")
                raise ValueError("Username not found")
            elif not self.remote_system_identity.password:
                log.error("Password not found")
                raise ValueError("Password not found")
            else:
                self._paho_client.username_pw_set(self.remote_system_identity.username, self.remote_system_identity.password)

        if self.qos_details:
            # Set QoS parameters
            self._paho_client.max_inflight_messages_set(self.qos_details.in_flight)
            self._paho_client.max_queued_messages_set(self.qos_details.queue_size)
            self._paho_client.message_retry_set(self.qos_details.retry)

        # Connect with MQTT Broker
        self._paho_client.connect(host=self.url, port=self.port, keepalive=self.keep_alive)

        # Start network loop to handle auto-reconnect
        self._paho_client.loop_start()
        ten_ms_count = 0
        while (ten_ms_count != self._conn_disconn_timeout * 100) and (self._connect_result_code == sys.maxsize):
            ten_ms_count += 1
            time.sleep(0.01)
        if self._connect_result_code == sys.maxsize:
            log.error("Connection timeout.")
            #  Stopping background network loop as connection establishment failed.
            self._paho_client.loop_stop()
            raise Exception("Connection Timeout")
        elif self._connect_result_code == 0:
            log.info("Connected to MQTT Broker.")
            log.info("Connect time consumption: " + str(float(ten_ms_count) * 10) + "ms.")
        else:
            log.error("Connection error with result code : {0} : {1} ".
                      format(str(self._connect_result_code), paho.connack_string(self._connect_result_code)))
            #  Stopping background network loop as connection establishment failed.
            self._paho_client.loop_stop()
            raise Exception("Connection error with result code : {0} : {1} ".
                      format(str(self._connect_result_code), paho.connack_string(self._connect_result_code)))

    def publish(self, topic, message, qos, retain=False):
        """
        Publishes message to the MQTT Broker

        :param topic: Publish topic
        :param message: Message to be published
        :param qos: Publish QoS
        :param retain: Message to be retained or not
        :return:
        """
        try:
            mess_info = self._paho_client.publish(topic, message, qos, retain)
            log.info("Publishing Message ID : {0} with result code : {1} ".format(mess_info.mid, mess_info.rc))
            log.debug("Published Topic:{0}, Payload:{1}, QoS:{2}".format(topic, message, qos))
        except Exception:
            log.exception("MQTT Publish exception traceback..")

    def subscribe(self, topic, qos, callback):
        """
        Subscribes to a topic with given callback

        :param topic: Subscribe topic
        :param qos: Subscribe QoS
        :param callback:  Callback for the topic
        :return:
        """
        try:
            subscribe_response = self._paho_client.subscribe(topic, qos)
            self._paho_client.message_callback_add(topic, callback)
            log.info("Topic subscribed with information: " + str(subscribe_response))
        except Exception:
            log.exception("MQTT subscribe exception traceback..")

    def disconnect(self):
        """
        Disconnects from MQTT Broker
        :return:
        """
        self._paho_client.disconnect()
        ten_ms_count = 0
        while (ten_ms_count != self._conn_disconn_timeout * 100) and (self._disconnect_result_code == sys.maxsize):
            ten_ms_count += 1
            time.sleep(0.01)
        if self._disconnect_result_code == sys.maxsize:
            log.error("Disconnect timeout.")
            raise Exception("Disconnection Timeout")
        elif self._disconnect_result_code == 0:
            log.info("Disconnected from MQTT Broker.")
            log.info("Disconnect time consumption: " + str(float(ten_ms_count) * 10) + "ms.")
            #  Disconnect is successful.  Stopping background network loop.
            self._paho_client.loop_stop()
        else:
            log.error("Disconnect error with result code : {0} : {1} ".
                      format(str(self._disconnect_result_code), paho.connack_string(self._disconnect_result_code)))
            raise Exception("Disconnect error with result code : {0} : {1} ".
                      format(str(self._disconnect_result_code), paho.connack_string(self._disconnect_result_code)))

    def get_client_id(self):
        """
        Returns client-id
        :return:
        """
        return self._paho_client._client_id


class QoSDetails:
    """
    Encapsulates config parameters related to Quality of Service
    """
    def __init__(self, in_flight, queue_size, retry):
        """
        :param in_flight: Set maximum no. of messages with QoS>0 that can be part way
                          through their network flow at once. Default is 20.
        :param queue_size: Set the maximum number of messages in the outgoing message queue. 0 means unlimited.
        :param retry: Set the timeout in seconds before a message with QoS>0 is retried. 20 seconds by default.
        """
        self.in_flight = in_flight
        self.queue_size = queue_size
        self.retry = retry


class MqttMessagingAttributes:
    """
    Encapsulates MessagingAttributes related to MQTT.

     This class enables the following options for developers in LIOTA
     ----------------------------------------------------------------

     a) Use single publish and subscribe topic generated by LIOTA for an EdgeSystem, its Devices and its Metrics.
        - Publish topic for all Metrics will be 'liota/generated_local_uuid_of_edge_system'
        - Subscribe topic will be 'liota-resp/generated_local_uuid_of_edge_system'
     b) Use custom single publish and subscribe topic for an EdgeSystem, its Devices and Metrics.

     - In the above two cases, MQTT message's payload MUST be self-descriptive so that subscriber can subscribe
      process accordingly to a single topic by parsing payload.

     c) Use custom publish and subscribe topics for Metrics.
     - In this case, MQTT message's payload need not be self-descriptive.  Subscribers can subscribe to
     appropriate topics accordingly.

     d) Use combination of (a) and (c) or (b) and (c).

    """
    def __init__(self, edge_system_name=None, pub_topic=None, sub_topic=None, pub_qos=1, sub_qos=1, pub_retain=False,
                 sub_callback=None):
        """
        :param edge_system_name: Name of the EdgeSystem
        :param pub_topic: Publish topic of EdgeSystem or RegisteredMetric
        :param sub_topic: Subscribe topic of EdgeSystem or RegisteredMetric
        :param pub_qos: Publish QoS
        :param sub_qos: Subscribe QoS
        :param pub_retain: Publish Retain Flag
        :param sub_callback: Subscribe Callback
        """
        if edge_system_name:
            #  For ProjectICE and Non-ProjectICE, topics will be auto-generated if gw_name is not None
            self.pub_topic = 'liota/' + systemUUID().get_uuid(edge_system_name)
            self.sub_topic = 'liota-resp/' + systemUUID().get_uuid(edge_system_name)
        else:
            #  When gw_name is None, pub_topic or sub_topic must be provided
            self.pub_topic = pub_topic
            self.sub_topic = sub_topic

        #  This validation is when MqttMessagingAttributes is initialized for reg_metric
        #  Client can assign topics for each metrics at metric level
        #  It will be used either for publishing or subscribing but not both.
        if self.pub_topic is None and (self.sub_topic is None or sub_callback is None):
            log.error("Either (pub_topic can be None) or (sub_topic and sub_callback) can be None. But not both")
            raise ValueError("Either (pub_topic can be None) or (sub_topic and sub_callback) can be None. But not both")

        #  General validation
        if pub_qos not in range(0, 3) or sub_qos not in range(0, 3):
            log.error("QoS should either be 0 or 1 or 2")
            raise ValueError("QoS should either be 0 or 1 or 2")
        if not isinstance(pub_retain, bool):
            log.error("pub_retain must be a boolean")
            raise ValueError("pub_retain must be a boolean")
        if sub_callback is not None:
            if not callable(sub_callback):
                log.error("sub_callback should either be None or callable")
                raise ValueError("sub_callback should either be None or callable")

        log.info("Pub Topic is:{0}".format(self.pub_topic))
        log.info("Sub Topic is:{0}".format(self.sub_topic))
        self.pub_qos = pub_qos
        self.sub_qos = sub_qos
        self.pub_retain = pub_retain
        self.sub_callback = sub_callback
