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
import psutil
from liota.core.package_manager import LiotaPackage

dependencies = ["aws_iot"]


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


class PackageClass(LiotaPackage):
    #  TODO: CHECK Warning: could not de-register resource refs. Package Manager line No: 680

    def run(self, registry):
        import pint
        import copy
        from liota.entities.metrics.metric import Metric
        from liota.entities.devices.simulated_device import SimulatedDevice

        # create a pint unit registry
        ureg = pint.UnitRegistry()

        # Acquire resources from registry
        aws_iot = registry.get("aws_iot")
        aws_iot_edge_system = copy.copy(registry.get("aws_iot_edge_system"))

        # Create metrics
        self.metrics = []
        metric_cpu_utilization = Metric(
            name="CPUUtilization",
            unit=None,
            interval=5,
            aggregation_size=1,
            sampling_function=read_cpu_utilization
        )
        reg_metric_cpu_utilization = aws_iot.register_entity(aws_iot_edge_system, metric_cpu_utilization)
        reg_metric_cpu_utilization.start_collecting()
        self.metrics.append(reg_metric_cpu_utilization)

        #  Creating Simulated Device
        dht_sensor = SimulatedDevice("SimulatedDHTSensor")
        #  Registering Device and creating Parent-Child relationship
        reg_dht_sensor = aws_iot.register_entity(aws_iot_edge_system, dht_sensor)

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
        reg_temp_metric = aws_iot.register_entity(reg_dht_sensor, temp_metric)
        #  Publishing Registered Temperature Metric to AWS
        reg_temp_metric.start_collecting()
        self.metrics.append(reg_temp_metric)

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
        reg_hum_metric = aws_iot.register_entity(reg_dht_sensor, hum_metric)
        #  Publishing Registered Humidity Metric to AWS
        reg_hum_metric.start_collecting()
        self.metrics.append(reg_hum_metric)

        #  Creating Simulated Device
        light_sensor = SimulatedDevice("SimDigLightSensor")
        #  Registering Device and creating Parent-Child relationship
        reg_light_sensor = aws_iot.register_entity(aws_iot_edge_system, light_sensor)

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
        reg_light_metric = aws_iot.register_entity(reg_light_sensor, light_metric)
        #  Publishing Registered Light Metric to AWS
        reg_light_metric.start_collecting()
        self.metrics.append(reg_light_metric)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()