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

import random

from liota.dcc_comms.mqtt_dcc_comms import MqttDccComms
from liota.lib.transports.mqtt import MqttMessagingAttributes
from liota.dccs.generic_mqtt import GenericMqtt
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.simulated_edge_system import SimulatedEdgeSystem

# getting values from conf file
config = {}
execfile('aws_iot/sampleProp.conf', config)


# Random number generator, simulating random metric readings.
def simulated_sampling_function():
    return random.randint(0, 20)

# ---------------------------------------------------------------------------
# In this example, we demonstrate how data for a simulated metric generating
# random numbers can be directed to MQTT Broker data center component using Liota.
# The program illustrates the ease of use Liota brings to IoT application
# developers.

if __name__ == '__main__':

    edge_system = SimulatedEdgeSystem(config['EdgeSystemName'])

    #  Connecting to MQTT Broker
    #  Initializing GenericMqtt DCC using MqttDccComms
    mqtt_broker = GenericMqtt(MqttDccComms(edge_system_name=edge_system.name,
                                           url=config['BrokerIP'], port=config['BrokerPort']))
    #  Registering EdgeSystem
    graphite_reg_edge_system = mqtt_broker.register(edge_system)

    metric_name = config['MetricName']
    simulated_metric = Metric(name=metric_name,
                              interval=5,
                              sampling_function=simulated_sampling_function)
    reg_metric = mqtt_broker.register(simulated_metric)
    mqtt_broker.create_relationship(graphite_reg_edge_system, reg_metric)
    #  Publish topic for this Metric
    reg_metric.msg_attr = MqttMessagingAttributes(pub_topic=config['CustomPubTopic'])
    reg_metric.start_collecting()

