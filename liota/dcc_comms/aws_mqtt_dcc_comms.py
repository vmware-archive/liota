
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
import sys
from dcc_comms import DCCComms
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

log = logging.getLogger(__name__)


class AWSMQTTDccComms(DCCComms):
    """
        This DCCComms leverages AWS provided device SDK.
        https://github.com/aws/aws-iot-device-sdk-python

        AWS SDK built on top of a modified Paho MQTT Python client library.

        Key features of AWS SDK are:
        1. Progressive reconnect back off
        2. Offline Publish requests queueing with Draining
        3. Persistent/Non-Persistent subscription
        4. Device shadow with token and version tracing
        5. MQTT over WebSocket with IAM/SigV4
    """

    def __init__(self, mqtt_client):
        #  Validating client type
        if isinstance(mqtt_client, AWSIoTMQTTClient) or isinstance(mqtt_client, AWSIoTMQTTShadowClient):
            self.mqtt_client = mqtt_client
        else:
            raise TypeError("AWSIoTMQTTClient or AWSIoTMQTTShadowClient is expected.")
        self._connect()

    def _connect(self):
        try:
            self.mqtt_client.connect()
            log.debug("Connected to AWS IoT")
        except Exception:
            log.exception("AWSIoT Connection Exception traceback")
            sys.exit(0)

    def _disconnect(self):
        if self.mqtt_client:
            self.mqtt_client.disconnect()
        log.debug("Disconnected")

    def publish(self, topic, payload, qos=1):
        try:
            if isinstance(self.mqtt_client, AWSIoTMQTTClient):
                #  Publish using AWSIoTMQTTClient
                self.mqtt_client.publish(topic, payload, qos)
            else:
                #  Publish using AWSIoTMQTTShadowClient
                self.mqtt_client.getMQTTConnection().publish(topic, payload, qos)
            log.debug("Published Topic:{0}, Payload:{1}, QoS:{2}".format(topic, payload, qos))
        except Exception:
            log.exception("AWSIoT Exception while publishing "
                          "Topic:{0}, Payload:{1}, QoS:{2}".format(topic, payload, qos))

    def subscribe(self):
        raise NotImplementedError

    def send(self, message):
        raise NotImplementedError

    def receive(self):
        raise NotImplementedError
