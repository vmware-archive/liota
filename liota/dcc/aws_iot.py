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


from liota.dcc.dcc_base import DataCenterComponent
from liota.core.metric_handler import MessagingAttributes
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import logging

log = logging.getLogger(__name__)


class AWSIoT(DataCenterComponent):
    """ DCC for AWS IoT platform.

        This DCC leverages AWS provided device SDK and its transport.
         https://github.com/aws/aws-iot-device-sdk-python

        AWS SDK built on top of a modified Paho MQTT Python client library.

        Key features of AWS SDK are:
        1. Progressive reconnect back off
        2. Offline Publish requests queueing with Draining
        3. Persistent/Non-Persistent subscription
        4. Device shadow with token and version tracing
        5. MQTT over WebSocket with IAM/SigV4
    """

    def __init__(self, aws_mqtt_client):
        """
        AWS DCC uses either AWSIoTMQTTClient or AWSIoTMQTTShadowClient to publish messages.

        :param aws_mqtt_client: AWSIoTMQTTClient or AWSIoTMQTTShadowClient
        """

        #  Validating client type
        if isinstance(aws_mqtt_client, AWSIoTMQTTClient) or isinstance(aws_mqtt_client, AWSIoTMQTTShadowClient):
            self.aws_mqtt_client = aws_mqtt_client
        else:
            raise TypeError("AWSIoTMQTTClient or AWSIoTMQTTShadowClient is expected.")

    def publish(self, metric):
        """
        Publishes message to AWS IoT in JSON format.

        :param metric: Metric object in liota/core/metric_handler.py
        :return: None
        """

        messaging_attributes = metric.messaging_attributes
        for t, v in metric.values:
            #  Though MQTT message has timestamp, we are sending it with payload because this timestamp denotes the time
            #  at which data is collected.  It would be useful if aggregation size is greater than one
            payload = {'details': metric.details, 'value': v, 'unit': metric.unit, 'timestamp': t}
            #  Payload is sent in JSON format
            payload = json.dumps(payload)
            log.info("Sending message: {0}".format(payload))
            if isinstance(self.aws_mqtt_client, AWSIoTMQTTClient):
                #  Publish using AWSIoTMQTTClient
                self.aws_mqtt_client.publish(messaging_attributes.topic, payload, messaging_attributes.qos)
            else:
                #  Publish using AWSIoTMQTTShadowClient
                self.aws_mqtt_client.getMQTTConnection().publish(messaging_attributes.topic, payload, messaging_attributes.qos)

    def subscribe(self):
        """
        For later implementation.

        :return: None
        """
        pass

    def create_messaging_attributes(self, topic, qos=1, callback=None):
        """
        Creates AWSIoTMessagingAttributes that will be passed to create_metric method in liota/dcc/dcc_base.py

        For each and every publish topic AWSIoTMessagingAttributes has to be created using this method

        :param topic: MQTT publish/subscribe topic
        :param qos: MQTT publish/subcribe. QoS could either be 0 or 1.
        :param callback: MQTT subscribe callback
        :return: AWSIoTMessagingAttributes object
        """

        return AWSIoTMessagingAttributes(topic, qos, callback)

    def register(self, gw):
        #  Registering gateway
        aws_gateway = self.AWSIoTGateway(gw, True)
        return aws_gateway

    class AWSIoTGateway:
        def __init__(self, gw, registered=False):
            self.resource = gw
            self.registered = registered


class AWSIoTMessagingAttributes(MessagingAttributes):
    """  This class holds AWS IoT specific messaging attributes
         that are unique to each publish or subscribe
    """

    def __init__(self, topic, qos, callback):
        """
        Attributes required to publish/subscribe to AWS IoT platform.

        :param topic: MQTT publish/subscribe topic
        :param qos: MQTT publish/subcribe QoS. QoS could either be 0 or 1.
        :param callback: AWSIoTMessagingAttributes object
        """

        # Required by both publish and subscribe
        MessagingAttributes.__init__(self, qos)
        # Required by both publish and subscribe
        self.topic = topic
        # Required by subscribe
        self.callback = callback
        # "retain" has been disabled and "False" is being passed to underlying paho client in AWS SDK
        #self.retain = retain










