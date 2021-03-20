# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2015-2017 VMware, Inc. All Rights Reserved.                    #
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

from liota.core.package_manager import LiotaPackage
from liota.lib.utilities.utility import read_user_config

dependencies = ["examples/mqtt/iotcc/iotcc_mqtt_edge_system_stats", "devices/sensor_tag"]


def get_ambient_temperature(sensor):
    tmp = sensor.get_temperature()
    return tmp[0] if tmp else None


def get_relative_humidity(sensor):
    hum = sensor.get_humidity()
    return hum[1] if hum else None


def get_pressure(sensor):
    # 1 millibar = 100 Pascal
    pressure = sensor.get_barometer()
    return (pressure[1] * 100) if pressure else None


def get_battery_level(sensor):
    return sensor.get_battery_level()


def get_light_level(sensor):
    return sensor.get_light_level()


class PackageClass(LiotaPackage):
    def run(self, registry):
        import copy
        import pint
        from liota.entities.metrics.metric import Metric

        # create a pint unit registry
        ureg = pint.UnitRegistry()

        # Acquire resources from registry
        self.iotcc_edge_system = copy.copy(registry.get("iotcc_edge_system"))
        self.iotcc = registry.get("iotcc_mqtt")
        self.sensor_tag = registry.get("sensor_tag_device")

        # Get values from configuration file
        config_path = registry.get("package_conf")
        self.config = read_user_config(config_path + '/sampleProp.conf')

        # Registering SensorTagDevice with IoTCC
        self.reg_sensor_tag = self.iotcc.register(self.sensor_tag)
        self.iotcc.create_relationship(self.iotcc_edge_system, self.reg_sensor_tag)

        # Create metrics
        self.metrics = []
        temperature_metric = Metric(
            name="AmbientTemperature",
            unit=ureg.degC,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_ambient_temperature(self.sensor_tag)
        )
        reg_temperature_metric = self.iotcc.register(temperature_metric)
        self.iotcc.create_relationship(self.reg_sensor_tag, reg_temperature_metric)
        reg_temperature_metric.start_collecting()
        self.metrics.append(reg_temperature_metric)

        humidity_metric = Metric(
            name="RelativeHumidity",
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_relative_humidity(self.sensor_tag)
        )
        reg_humidity_metric = self.iotcc.register(humidity_metric)
        self.iotcc.create_relationship(self.reg_sensor_tag, reg_humidity_metric)
        reg_humidity_metric.start_collecting()
        self.metrics.append(reg_humidity_metric)

        pressure_metric = Metric(
            name="Pressure",
            unit=ureg.Pa,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_pressure(self.sensor_tag)
        )
        reg_pressure_metric = self.iotcc.register(pressure_metric)
        self.iotcc.create_relationship(self.reg_sensor_tag, reg_pressure_metric)
        reg_pressure_metric.start_collecting()
        self.metrics.append(reg_pressure_metric)

        battery_level_metric = Metric(
            name=str(self.config['DeviceName'])+'-BatteryLevel',
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_battery_level(self.sensor_tag)
        )
        reg_battery_level_metric = self.iotcc.register(battery_level_metric)
        self.iotcc.create_relationship(self.reg_sensor_tag, reg_battery_level_metric)
        reg_battery_level_metric.start_collecting()
        self.metrics.append(reg_battery_level_metric)

        light_metric = Metric(
            name="LightLevel",
            unit=ureg.lx,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_light_level(self.sensor_tag)
        )
        reg_light_metric = self.iotcc.register(light_metric)
        self.iotcc.create_relationship(self.reg_sensor_tag, reg_light_metric)
        reg_light_metric.start_collecting()
        self.metrics.append(reg_light_metric)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()

        self.sensor_tag.stop_collecting()

        # Unregister iotcc device
        if self.config['ShouldUnregisterOnUnload'] == "True":
            self.iotcc.unregister(self.reg_sensor_tag)
