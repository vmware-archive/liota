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

from liota.dcc_comms.aws_mqtt_dcc_comms import AWSMQTTDccComms
from liota.dccs.aws_iot import AWSIoT
from liota.entities.metrics.metric import Metric
from liota.entities.devices.device import Device
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
import random
import pint
import psutil

# getting aws related values from conf file
aws_conf = {}
execfile('awsSampleProp.conf', aws_conf)

# create a pint unit registry
ureg = pint.UnitRegistry()


#  Reading CPU Utilization.
def read_cpu_utilization(sample_duration_sec=1):
    return round(psutil.cpu_percent(interval=sample_duration_sec), 2)


#  Random number generator, simulating living room temperature readings.
def living_room_temperature():
    return random.randint(10, 30)


#  Random number generator, simulating living room humidity readings.
def living_room_humidity():
    return random.randint(70, 90)


#  Random number generator, simulating living room luminous readings.
def living_room_luminance():
    # 0 - Lights Off, 1 - Lights On
    return random.randint(0, 1)

# ---------------------------------------------------------------------------------
# In this example, we demonstrate how data for a simulated metric generating
# random numbers can be directed to AWS IoT data center component using Liota.
#
# A Simulated DHT sensor with Temperature and Humidity Metrics and a Simulated
# Digital Light sensor with binary luminance Metrics are used.
#
# Liota uses AWSIoT SDK which uses MQTT as transport. Developers need not provide
# MQTT tropics explicitly.  Publish topics are derived from Entity hierarchy
# structure of Liota and slash separated Entity names are used as publish topics.
#
#
#                                            Dell5kEdgeSystem
#                                                   |
#                                                   |
#                                                   |
#                     -----------------------------------------------------
#                    |                              |                      |
#                    |                              |                      |
#                    |                              |                      |
#                 DHT Sensor                 Digital Light Sensor    CPU Utilization
#                    |                              |                   Metric
#                    |                              |
#            ----------------                  Light Metric
#           |                |
#           |                |
#      Temperature        Humidity
#         Metric           Metric
#
# The program illustrates the ease of use and manageability that Liota
# brings to IoT application developers.


if __name__ == '__main__':
    #  Creating EdgeSystem
    edge_system = Dell5KEdgeSystem(aws_conf['GatewayName'])

    #  These are standard steps to be followed to connect with AWS IoT using AWS IoT SDK
    mqtt_client = AWSIoTMQTTClient(aws_conf['GatewayName'])
    mqtt_client.configureEndpoint(aws_conf['AWSEndpoint'], aws_conf['AWSPort'])
    mqtt_client.configureCredentials(aws_conf['RootCAPath'], aws_conf['PrivateKeyPath'], aws_conf['ClientCertPath'])
    mqtt_client.configureConnectDisconnectTimeout(aws_conf['ConnectDisconnectTimeout'])
    mqtt_client.configureMQTTOperationTimeout(aws_conf['OperationTimeout'])

    #  Initializing AWSMQTTDccComms with AWSIoT client object
    #  Connecting to AWS
    #  Initializing AWS DCC using AWSMQTTDccComms object. QoS is 1 by default
    aws = AWSIoT(AWSMQTTDccComms(mqtt_client))
    print "Connected to AWS !"
    #  Registering EdgeSystem
    reg_edge_system = aws.register_entity(edge_system, None)

    #  Creating CPU Metric
    cpu_utilization = Metric(
        name="CPUUtilization",
        unit=None,
        interval=10,
        aggregation_size=2,
        sampling_function=read_cpu_utilization
    )
    #  Registering Metric and creating Parent-Child relationship
    reg_cpu_utilization = aws.register_entity(reg_edge_system, cpu_utilization)
    #  Publishing Registered CPU Utilization Metric to AWS
    #  at topic 'TestGatewayName/CPUUtilization'
    reg_cpu_utilization.start_collecting()

    #  Creating Device
    dht_sensor = Device("SimulatedDHTSensor", None)
    #  Registering Device and creating Parent-Child relationship
    reg_dht_sensor = aws.register_entity(reg_edge_system, dht_sensor)
    #  Creating Temperature Metric
    temp_metric = Metric(
        name="LivingRoomTemperature",
        entity_type="Metric",
        unit=ureg.degC,
        interval=1,
        aggregation_size=5,
        sampling_function=living_room_temperature
    )
    #  Registering Metric and creating Parent-Child relationship
    reg_temp_metric = aws.register_entity(reg_dht_sensor, temp_metric)
    #  Publishing Registered Temperature Metric to AWS
    #  at topic 'TestGatewayName/SimulatedDHTSensor/LivingRoomTemperature'
    reg_temp_metric.start_collecting()

    #  Creating Humidity Metric
    hum_metric = Metric(
        name="LivingRoomHumidity",
        entity_type="Metric",
        unit=None,
        interval=1,
        aggregation_size=5,
        sampling_function=living_room_humidity
    )
    #  Registering Metric and creating Parent-Child relationship
    reg_hum_metric = aws.register_entity(reg_dht_sensor, hum_metric)
    #  Publishing Registered Humidity Metric to AWS
    #  at topic 'TestGatewayName/SimulatedDHTSensor/LivingRoomHumidity'
    reg_hum_metric.start_collecting()

    #  Creating Device
    light_sensor = Device("SimDigLightSensor", None)
    #  Registering Device and creating Parent-Child relationship
    reg_light_sensor = aws.register_entity(reg_edge_system, light_sensor)

    #  Creating Light Metric
    light_metric = Metric(
        name="LivingRoomLight",
        entity_type="Metric",
        unit=None,
        interval=10,
        aggregation_size=1,
        sampling_function=living_room_luminance
    )
    #  Registering Metric and creating Parent-Child relationship
    reg_light_metric = aws.register_entity(reg_light_sensor, light_metric)
    #  Publishing Registered Light Metric to AWS
    #  at topic 'TestGatewayName/SimDigLightSensor/LivingRoomLight'
    reg_light_metric.start_collecting()
