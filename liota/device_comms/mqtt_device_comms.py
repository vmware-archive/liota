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

    def __init__(self, edge_system_identity, tls_details, qos_details, url, port, keepalive = 60, enable_authentication = True):
        self.edge_system_identity = edge_system_identity
        self.tls_details = tls_details
        self.url = url
        self.port = port
        self.keepalive = keepalive
        self.qos_details = qos_details
        self.enable_authentication = enable_authentication
        self._connect()

    # Connect with MQTT broker
    def _connect(self):
        self.mqtt_client = Mqtt(self.edge_system_identity, self.tls_details, self.qos_details, self.url, self.port,
                                self.keepalive, self.enable_authentication)

    # Disconnect method
    def _disconnect(self):
        self.mqtt_client.disconnect()

    # Publish Method
    def publish(self, topic, message, qos, retain = False):
        self.mqtt_client.publish(topic, message, qos, retain)

    # Subscribe Method
    def subscribe(self, topic, qos, callback):
        self.mqtt_client.subscribe(topic, qos, callback)

    def send(self, message):
        raise NotImplementedError

    def receive(self):
        raise NotImplementedError
