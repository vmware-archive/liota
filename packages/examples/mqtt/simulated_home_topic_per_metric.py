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

from linux_metrics import cpu_stat

from liota.core.package_manager import LiotaPackage

dependencies = ["generic_mqtt"]


#  Reading CPU Utilization.
def read_cpu_utilization(sample_duration_sec=1):
    cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
    return round((100 - cpu_pcts['idle']), 2)


#  Random number generator, simulating living room temperature readings.
def get_living_room_temperature():
    return random.randint(10, 30)


#  Random number generator, simulating living room humidity readings.
def get_living_room_humidity():
    return random.randint(70, 90)


#  Random number generator, simulating living room luminous readings.
def get_living_room_luminance():
    # 0 - Lights Off, 1 - Lights On
    return random.randint(0, 1)


# ------------------------------------------------------------------------------------------------------------------
# In this example, we demonstrate how data for a simulated metric generating
# random numbers can be directed to GenericMqtt data center component using Liota.
#
# A Simulated DHT sensor with Temperature and Humidity Metrics and a Simulated
# Digital Light sensor with binary luminance Metrics are used.
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
# Developers can leverage the following options:
# ---------------------------------------------
#  a) Use single publish and subscribe topic generated by LIOTA for an EdgeSystem, its Devices and its Metrics.
#  b) Use custom single publish and subscribe topic for an EdgeSystem, its Devices and Metrics.
#
#  - In the above two cases, MQTT message's payload MUST be self-descriptive so that subscriber can subscribe
#    process accordingly to a single topic by parsing payload.
#
#  c) Use custom publish and subscribe topics for Metrics.
#  - In this case, MQTT message's payload need not be self-descriptive.  Subscribers can subscribe to
#    appropriate topics and process accordingly.
#
#  d) Use combination of (a) and (c) or (b) and (c).
#
#
# GenericMqtt DCC has enclose_metadata option.  It can be used to enclose EdgeSystem, Device and Metric names
# along with the sensor data payload of a Metric.
#
# This example showcases publishing Metrics using (c) with enclose_metadata
# ----------------------------------------------------------------------------------------------------------------------

class PackageClass(LiotaPackage):
    def run(self, registry):
        import copy
        import pint

        from liota.lib.transports.mqtt import MqttMessagingAttributes
        from liota.entities.metrics.metric import Metric
        from liota.entities.devices.simulated_device import SimulatedDevice

        # create a pint unit registry
        ureg = pint.UnitRegistry()

        # Acquire resources from registry
        generic_mqtt = registry.get("generic_mqtt")
        generic_mqtt_edge_system = copy.copy(registry.get("generic_mqtt_edge_system"))

        # Get values from configuration file
        config_path = registry.get("package_conf")
        config = {}
        execfile(config_path + '/sampleProp.conf', config)

        # Create metrics
        self.metrics = []

        #  Creating CPU Metric
        cpu_utilization = Metric(
            name="CPUUtilization",
            unit=None,
            interval=10,
            aggregation_size=2,
            sampling_function=read_cpu_utilization
        )
        #  Registering Metric and creating Parent-Child relationship
        reg_cpu_utilization = generic_mqtt.register(cpu_utilization)
        generic_mqtt.create_relationship(generic_mqtt_edge_system, reg_cpu_utilization)
        #  Publish topic for this Metric
        reg_cpu_utilization.msg_attr = MqttMessagingAttributes(pub_topic=config['CustomPubTopic'])
        #  Publishing Registered CPU Utilization Metric to GenericMqtt Dcc
        reg_cpu_utilization.start_collecting()
        self.metrics.append(reg_cpu_utilization)

        #  Creating Simulated Device
        dht_sensor = SimulatedDevice("SimulatedDHTSensor")
        #  Registering Device and creating Parent-Child relationship
        reg_dht_sensor = generic_mqtt.register(dht_sensor)
        generic_mqtt.create_relationship(generic_mqtt_edge_system, reg_dht_sensor)
        #  Creating Temperature Metric
        temp_metric = Metric(
            name="LivingRoomTemperature",
            entity_type="Metric",
            unit=ureg.degC,
            interval=1,
            aggregation_size=5,
            sampling_function=get_living_room_temperature
        )
        #  Registering Metric and creating Parent-Child relationship
        reg_temp_metric = generic_mqtt.register(temp_metric)
        generic_mqtt.create_relationship(reg_dht_sensor, reg_temp_metric)
        #  Publish topic for this Metric
        reg_temp_metric.msg_attr = MqttMessagingAttributes(pub_topic=config['LivingRoomTemperatureTopic'])
        #  Publishing Registered Temperature Metric to GenericMqtt Dcc
        reg_temp_metric.start_collecting()
        self.metrics.append(reg_temp_metric)

        #  Creating Humidity Metric
        hum_metric = Metric(
            name="LivingRoomHumidity",
            entity_type="Metric",
            unit=None,
            interval=1,
            aggregation_size=5,
            sampling_function=get_living_room_humidity
        )
        #  Registering Metric and creating Parent-Child relationship
        reg_hum_metric = generic_mqtt.register(hum_metric)
        generic_mqtt.create_relationship(reg_dht_sensor, reg_hum_metric)
        #  Publish topic for this Metric
        reg_hum_metric.msg_attr = MqttMessagingAttributes(pub_topic=config['LivingRoomHumidityTopic'])
        #  Publishing Registered Humidity Metric to GenericMqtt Dcc
        reg_hum_metric.start_collecting()
        self.metrics.append(reg_hum_metric)

        #  Creating Simulated Device
        light_sensor = SimulatedDevice("SimDigLightSensor")
        #  Registering Device and creating Parent-Child relationship
        reg_light_sensor = generic_mqtt.register(light_sensor)
        generic_mqtt.create_relationship(generic_mqtt_edge_system, reg_light_sensor)

        #  Creating Light Metric
        light_metric = Metric(
            name="LivingRoomLight",
            entity_type="Metric",
            unit=None,
            interval=10,
            aggregation_size=1,
            sampling_function=get_living_room_luminance
        )
        #  Registering Metric and creating Parent-Child relationship
        reg_light_metric = generic_mqtt.register(light_metric)
        generic_mqtt.create_relationship(reg_light_sensor, reg_light_metric)
        #  Publish topic for this Metric
        reg_light_metric.msg_attr = MqttMessagingAttributes(pub_topic=config['LivingRoomLightTopic'])
        #  Publishing Registered Light Metric to GenericMqttDcc
        reg_light_metric.start_collecting()
        self.metrics.append(reg_light_metric)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()
