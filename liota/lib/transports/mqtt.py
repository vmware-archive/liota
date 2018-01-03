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
try:
    import ssl
except ImportError:
    ssl = None
import sys
import time

import paho.mqtt.client as paho

from liota.lib.utilities.utility import systemUUID, read_liota_config

log = logging.getLogger(__name__)


class Mqtt():
    """
    MQTT Transport implementation for LIOTA. It internally uses Python Paho library.
    """

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
        :param granted_qos: Granted QoS by the broker
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

    def __init__(self, url, port, identity=None, tls_conf=None, qos_details=None, client_id=None,
                 clean_session=False, userdata=None, protocol="MQTTv311", transport="tcp", keep_alive=60,
                 enable_authentication=False, conn_disconn_timeout=int(read_liota_config('MQTT_CFG', 'mqtt_conn_disconn_timeout'))):

        """
        :param url: MQTT Broker URL or IP
        :param port: MQTT Broker Port
        :param identity: Identity Object
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
        :param username: Username for authentication
        :param password: Password for authentication
        :param conn_disconn_timeout: Connect-Disconnect-Timeout
        """
        self.url = url
        self.port = port
        self.identity = identity
        self.tls_conf = tls_conf
        self.qos_details = qos_details
        self.client_id = client_id
        self.clean_session = clean_session
        self.userdata = userdata
        self.protocol = protocol
        self.transport = transport
        self.keep_alive = keep_alive
        self.enable_authentication = enable_authentication
        self._conn_disconn_timeout = conn_disconn_timeout
        self._paho_client = paho.Client(self.client_id, self.clean_session, self.userdata,
                                        protocol=getattr(paho, self.protocol), transport=self.transport)
        self._connect_result_code = sys.maxsize
        self._disconnect_result_code = sys.maxsize
        self._paho_client.on_message = self.on_message
        self._paho_client.on_publish = self.on_publish
        self._paho_client.on_subscribe = self.on_subscribe
        self._paho_client.on_connect = self.on_connect
        self._paho_client.on_disconnect = self.on_disconnect
        self.sub_dict = {}
        self.connect_soc()

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
        for topic in self.sub_dict:
            self.subscribe(topic, self.sub_dict.get(topic)[0], self.sub_dict.get(topic)[1])
            log.info("Re-Subscribed to topic : {0} after re-connection".format(topic))

    def connect_soc(self):
        """
        Establishes connection with MQTT Broker
        :return:
        """
        # Set up TLS support
        if self.tls_conf:

            if self.identity is None:
                raise ValueError("Identity required to be set")

            # Creating the tls context
            if ssl is None:
                raise ValueError("This platform has no SSL/TLS")

            # Validate CA certificate path
            if self.identity.root_ca_cert is None and not hasattr(ssl.SSLContext, 'load_default_certs'):
                raise ValueError("Error : CA certificate path is missing")
            else:
                if self.identity.root_ca_cert and not (os.path.exists(self.identity.root_ca_cert)):
                    raise ValueError("Error : Wrong CA certificate path")

            if self.tls_conf.tls_version is None:
                tls_version = ssl.PROTOCOL_TLSv1_2
                # If the python version supports it, use highest TLS version automatically
                if hasattr(ssl, "PROTOCOL_TLS"):
                    tls_version = ssl.PROTOCOL_TLS
            else:
                tls_version = getattr(ssl, self.tls_conf.tls_version)
            context = ssl.SSLContext(tls_version)

            # Validate client certificate path
            if self.identity.cert_file:
                if os.path.exists(self.identity.cert_file):
                    client_cert_available = True
                else:
                    raise ValueError("Error : Wrong client certificate path")
            else:
                client_cert_available = False

            # Validate client key file path
            if self.identity.key_file:
                if os.path.exists(self.identity.key_file):
                    client_key_available = True
                else:
                    raise ValueError("Error : Wrong client key path.")
            else:
                client_key_available = False

            '''
                Multiple conditions for certificate validations
                # 1. Both Client certificate and key file should be present
                # 2. If client certificate is not there throw an error
                # 3. If client key is not there throw an error
                # 4. If both are not there proceed without client certificate and key
            '''
            if client_cert_available and client_key_available:
                context.load_cert_chain(self.identity.cert_file, self.identity.key_file)
            elif not client_cert_available and client_key_available:
                raise ValueError("Error : Client key found, but client certificate not found")
            elif client_cert_available and not client_key_available:
                raise ValueError("Error : Client certificate found, but client key not found")
            else:
                log.info("Client Certificate and Client Key are not provided")

            if getattr(ssl, self.tls_conf.cert_required) == ssl.CERT_NONE and hasattr(context, 'check_hostname'):
                context.check_hostname = False

            context.verify_mode = ssl.CERT_REQUIRED if self.tls_conf.cert_required is None else getattr(ssl,
                                                                                                        self.tls_conf.cert_required)

            if self.identity.root_ca_cert is not None:
                context.load_verify_locations(self.identity.root_ca_cert)
            else:
                context.load_default_certs()

            if self.tls_conf.cipher is not None:
                context.set_ciphers(self.tls_conf.ciphers)

            # Setting the verify_flags to VERIFY_CRL_CHECK_CHAIN in this mode
            # certificate revocation lists (CRLs) of all certificates in the
            # peer cert chain are checked if the path of CRLs in PEM or DER format
            # is specified
            crl_path = read_liota_config('CRL_PATH', 'crl_path')
            if crl_path and crl_path != "None" and crl_path != "":
                if os.path.exists(crl_path):
                    context.verify_flags = ssl.VERIFY_CRL_CHECK_CHAIN
                    context.load_verify_locations(cafile=crl_path)
                else:
                    raise ValueError("Error : Wrong Client CRL path {0}".format(crl_path))

            # Setting the tls context
            self._paho_client.tls_set_context(context)

            if getattr(ssl, self.tls_conf.cert_required) != ssl.CERT_NONE:
                # Default to secure, sets context.check_hostname attribute
                # if available
                self._paho_client.tls_insecure_set(False)
            else:
                # But with ssl.CERT_NONE, we can not check_hostname
                self._paho_client.tls_insecure_set(True)
        else:
            log.info("TLS configuration is not set")


        # Set up username-password
        if self.enable_authentication:
            if self.identity is None:
                raise ValueError("Identity required to be set")
            else:
                if self.identity.username is None:
                    raise ValueError("Username not found")
                elif self.identity.password is None:
                    raise ValueError("Password not found")
                else:
                    self._paho_client.username_pw_set(self.identity.username, self.identity.password)
        else:
            log.info("Authentication is disabled")

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
        mess_info = self._paho_client.publish(topic, message, qos, retain)
        if mess_info.rc == 0:
            log.debug("Published Message ID:{0} with result code:{1}, Topic:{2}, Payload:{3}, QoS:{4}".format(mess_info.mid, mess_info.rc, topic, message, qos))
        else:
            raise Exception("MQTT Publish exception Message ID:{0} with result code:{1}, Topic:{2}, Payload:{3}, QoS:{4}".format(mess_info.mid, mess_info.rc, topic, message, qos))

    def subscribe(self, topic, qos, callback):
        """
        Subscribes to a topic with given callback

        :param topic: Subscribe topic
        :param qos: Subscribe QoS
        :param callback:  Callback for the topic
        :return:
        """
        try:
            self.sub_dict.setdefault(topic, [qos, callback])
            subscribe_response = self._paho_client.subscribe(topic, qos)
            self._paho_client.message_callback_add(topic, callback)
            log.info("Topic subscribed with information: " + str(subscribe_response))
        except Exception:
            log.exception("MQTT subscribe exception traceback..")

    def unsubscribe(self, topic):
        """
        Unsubscribes to a topic

        :param topic: Unsubscribe topic
        :return:
        """
        try:
            self.sub_dict.pop(topic, None)
            unsubscribe_response = self._paho_client.unsubscribe(topic)
            self._paho_client.message_callback_remove(topic)
            log.info("Topic unsubscribed with information: " + str(unsubscribe_response))
        except Exception:
            log.exception("MQTT unsubscribe exception traceback..")

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
            raise Exception("Disconnection Timeout")
        elif self._disconnect_result_code == 0:
            log.info("Disconnected from MQTT Broker.")
            log.info("Disconnect time consumption: " + str(float(ten_ms_count) * 10) + "ms.")
            #  Disconnect is successful.  Stopping background network loop.
            self._paho_client.loop_stop()
        else:
            raise Exception("Disconnect error with result code : {0} : {1} ".
                            format(str(self._disconnect_result_code),
                                   paho.connack_string(self._disconnect_result_code)))

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
        - Publish topic for all Metrics will be 'liota/generated_local_uuid_of_edge_system/request'
        - Subscribe topic will be 'liota/generated_local_uuid_of_edge_system/response'
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
            #  For Project ICE and Non-Project ICE, topics will be auto-generated if edge_system_name is not None
            self.pub_topic = 'liota/' + systemUUID().get_uuid(edge_system_name) + '/request'
            self.sub_topic = 'liota/' + systemUUID().get_uuid(edge_system_name) + '/response'
        else:
            #  When edge_system_name is None, pub_topic or sub_topic must be provided
            self.pub_topic = pub_topic
            self.sub_topic = sub_topic

        # General validation
        if pub_qos not in range(0, 3) or sub_qos not in range(0, 3):
            raise ValueError("QoS should either be 0 or 1 or 2")
        if not isinstance(pub_retain, bool):
            raise ValueError("pub_retain must be a boolean")
        if sub_callback is not None:
            if not callable(sub_callback):
                raise ValueError("sub_callback should either be None or callable")

        log.info("Pub Topic is:{0}".format(self.pub_topic))
        log.info("Sub Topic is:{0}".format(self.sub_topic))
        self.pub_qos = pub_qos
        self.sub_qos = sub_qos
        self.pub_retain = pub_retain
        self.sub_callback = sub_callback
