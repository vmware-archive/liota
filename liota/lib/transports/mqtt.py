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
import paho.mqtt.client as paho
import ssl

log = logging.getLogger(__name__)


# MQTT Class implementation
class Mqtt():

    # Invoked when the broker responds to subscribe request
    def on_subscribe(self, client, userdata, mid, granted_qos):
        log.debug("Subscribed: {0} {1}".format(str(mid), str(granted_qos)))

    # Invoked when message received on a subscribed topic
    def on_message(self, client, userdata, msg):
        log.debug("On Message {0} {1} {2}".format(msg.topic, str(msg.qos), str(msg.payload)))

    # Called when publish transmission completed
    def on_publish(self, client, userdata, mid):
        log.debug("mid: {0}".format(str(mid)))

    # Invoked on response from broker to connection request
    def on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            raise ValueError("Error: " + paho.connack_string(rc))
        else:
            log.debug("Connected with result code " + str(rc) + " : " + paho.connack_string(rc))

    # Initialization
    def __init__(self, edge_system_identity, tls_details, qos_details, url, port, keepalive = 60, enable_authentication = True):
        self.edge_system_identity = edge_system_identity
        self.tls_details = tls_details
        self.url = url
        self.port = port
        self.keepalive = keepalive
        self.qos_details = qos_details
        self.enable_authentication = enable_authentication
        self.client = paho.Client()
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe
        self.client.on_connect = self.on_connect
        self.connect_soc()

    # Method for connection establishment
    def connect_soc(self):
        # Set up TLS support
        if self.tls_details:

            # Validate CA certificate path
            if self.edge_system_identity.cacert:
                if not(os.path.exists(self.edge_system_identity.cacert)):
                    raise ValueError("Error : Wrong CA certificate path.")
            else:
                raise ValueError("Error : CA certificate path is missing")

            # Validate client certificate path
            if self.edge_system_identity.certfile:
                if os.path.exists(self.edge_system_identity.certfile):
                    client_cert_available = True
                else:
                    raise ValueError("Error : Wrong client certificate path.")
            else:
                client_cert_available = False

            # Validate client key file path
            if self.edge_system_identity.keyfile:
                if os.path.exists(self.edge_system_identity.keyfile):
                    client_key_available = True
                else:
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
                log.debug("Certificates : ", self.edge_system_identity.cacert, self.edge_system_identity.certfile, self.edge_system_identity.keyfile)

                self.client.tls_set(self.edge_system_identity.cacert, self.edge_system_identity.certfile, self.edge_system_identity.keyfile,
                                    cert_reqs=getattr(ssl, self.tls_details.cert_required),
                                    tls_version=getattr(ssl, self.tls_details.tls_version), ciphers=self.tls_details.cipher)
            elif not client_cert_available and not client_key_available:
                self.client.tls_set(self.edge_system_identity.cacert,
                                    cert_reqs=getattr(ssl, self.tls_details.cert_required),
                                    tls_version=getattr(ssl, self.tls_details.tls_version), ciphers=self.tls_details.cipher)
            elif not client_cert_available and client_key_available:
                raise ValueError("Error : Client key found, but client certificate not found")
            else:
                raise ValueError("Error : Client certificate found, but client key not found")

            log.info("TLS support is set up.")

        # Set up username-password
        if self.enable_authentication:
            if not self.edge_system_identity.username:
                raise ValueError("Username not found")
            elif not self.edge_system_identity.password:
                raise ValueError("Password not found")
            else:
                self.client.username_pw_set(self.edge_system_identity.username, self.edge_system_identity.password)

        if self.qos_details:
            # Set QoS parameters
            self.client.max_inflight_messages_set(self.qos_details.inflight)
            self.client.max_queued_messages_set(self.qos_details.queue_size)
            self.client.message_retry_set(self.qos_details.retry)

        # Connect with MQTT Broker
        self.client.connect(host=self.url, port=self.port, keepalive= self.keepalive)

    # Publish Method
    def publish(self, topic, message, qos, retain = False):
        try:
            publish_response = self.client.publish(topic, message, qos, retain)
            log.info("Message Sent with message information: " + str(publish_response))
        except ValueError as e:
            log.error("Error Occured: " + str(e))
            raise e

    # Subscribe Method
    def subscribe(self, topic, qos):
        try:
            subscribe_response = self.client.subscribe(topic, qos)
            log.info("Topic subscribed with information: " + str(subscribe_response))
        except ValueError as e:
            log.error("Error Ocuured: " + str(e))
            raise e

    # Disconnect Method
    def disconnect(self):
        self.client.disconnect()

# This class encapsulates configurations parameter related to Quality of Service
class QoSDetails:
    def __init__(self, inflight, queue_size, retry):
        self.inflight = inflight
        self.queue_size = queue_size
        self.retry = retry
