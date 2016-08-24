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
from transport_layer_base import TransportLayer

log = logging.getLogger(__name__)

class Mqtt(TransportLayer):

    def on_subscribe(self, client, userdata, mid, granted_qos):
        log.debug("Subscribed: {0} {1}".format(str(mid), str(granted_qos)))

    def on_message(self, client, userdata, msg):
        log.debug("On Message {0} {1} {2}".format(msg.topic, str(msg.qos), str(msg.payload)))

    def on_publish(self, client, userdata, mid):
        log.debug("mid: {0}".format(str(mid)))

    def on_connect(self, client, userdata, flags, rc):
        log.debug("Connected with result code " + str(rc))

    def __init__(self, gw_identity, TLSConf, url, port, keepalive, tls_support=True):
        self.gw_identity = gw_identity
        self.TLSConf = TLSConf
        self.url = url
        self.port = port
        self.keepalive = keepalive
        self.client = paho.Client()
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe
        self.tls_support = tls_support
        self.connect_soc()
        TransportLayer.__init__(self)

    def connect_soc(self):
        # Set up TLS support
        if self.tls_support:

            # Validate CA certificate path
            if self.gw_identity.cacert:
                if not(os.path.exists(self.gw_identity.cacert)):
                    raise ValueError("Error : Wrong CA certificate path.")
            else:
                raise ValueError("Error : CA certificate path is missing")

            # Validate client certificate path
            if self.gw_identity.certfile:
                if os.path.exists(self.gw_identity.certfile):
                    client_cert_available = True
                else:
                    raise ValueError("Error : Wrong client certificate path.")
            else:
                client_cert_available = False

            # Validate client key file path
            if self.gw_identity.keyfile:
                if os.path.exists(self.gw_identity.keyfile):
                    client_key_available = True
                else:
                    raise ValueError("Error : Wrong client key path.")
            else:
                client_key_available = False

            # Multiple conditions for certificate validations
                # 1. Both Client certificate and key file should be present
                # 2. If both are not there proceed without client certificate and key
                # 3. If client certificate is not there throw an error
                # 4. If client key is not there throw an error
            if client_cert_available and client_key_available:
                log.debug("Certificates : ", self.gw_identity.cacert, self.gw_identity.certfile, self.gw_identity.keyfile)

                self.client.tls_set(self.gw_identity.cacert, self.gw_identity.certfile, self.gw_identity.keyfile,
                                    cert_reqs=getattr(ssl, self.TLSConf.cert_required),
                                    tls_version=getattr(ssl, self.TLSConf.tls_version), ciphers=self.TLSConf.cipher)
            elif not client_cert_available and not client_key_available:
                self.client.tls_set(self.gw_identity.cacert,
                                    cert_reqs=getattr(ssl, self.TLSConf.cert_required),
                                    tls_version=getattr(ssl, self.TLSConf.tls_version), ciphers=self.TLSConf.cipher)
            elif not client_cert_available and client_key_available:
                raise ValueError("Error : Client key found, but client certificate not found")
            else:
                raise ValueError("Error : Client certificate found, but client key not found")

            log.info("TLS support is set up.")

        # Connect with MQTT Broker
        self.client.on_connect = self.on_connect
        self.client.connect(host=self.url, port=self.port, keepalive= self.keepalive)

    def publish(self, topic, message):
        self.client.publish(topic, message)
        log.info("Message Sent")

    def subscribe(self, topic):
        self.client.subscribe(topic, qos=1)
        self.client.loop_forever()