# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2017 VMware, Inc. All Rights Reserved.                         #
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

import pint

from liota.device_comms.mqtt_device_comms import MqttDeviceComms
from liota.entities.devices.device import Device
from liota.lib.utilities.utility import systemUUID


class MqttSubscription(Device):

    def __init__(self, name, topic, url=None, port=1883, ureg=None):
        super(MqttSubscription, self).__init__(
            name=name,
            entity_id=systemUUID().get_uuid(name),
            entity_type=self.__class__.__name__
        )
        self.log = logging.getLogger(__name__)

        self.port = port
        self.url = url
        self.qos = 1

        self.client = MqttDeviceComms(
            remote_system_identity=None,
            edge_system_identity=None,
            tls_details=None,
            qos_details=None,
            url=self.url,
            port=self.port,
            clean_session=True,
            client_id=systemUUID().get_uuid(name)
        )

        self.topic = topic
        self.ureg = None
        if isinstance(ureg, pint.UnitRegistry):
            self.ureg = ureg
        else:
            self.ureg = pint.UnitRegistry()

        self.run()

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4, width=1)

    def __repr__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4, width=1)

    def run(self):
        self.log.debug("calling subscribe on topic: " + self.topic)
        self.client.subscribe(self.topic, self.qos, callback=self._handle_msg)

    # callback to handle messages on subscribed topic
    def _handle_msg(self, client, userdata, msg):
        self.log.debug("client(%s) userdata(%s) got msg(%s,%s,%s)): "
                       % (client, userdata, str(msg.payload), str(msg.qos), str(msg.topic)))
