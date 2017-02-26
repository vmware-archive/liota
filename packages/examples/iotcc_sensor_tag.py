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

import pint
import math

from linux_metrics import cpu_stat, mem_stat

from liota.core.package_manager import LiotaPackage


dependencies = ["iotcc"]


# create a pint unit registry
ureg = pint.UnitRegistry()


def read_cpu_procs():
    return cpu_stat.procs_running()


def read_cpu_utilization(sample_duration_sec=1):
    cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
    return round((100 - cpu_pcts['idle']), 2)


def read_mem_free():
    total_mem = round(mem_stat.mem_stats()[1], 4)
    free_mem = round(mem_stat.mem_stats()[3], 4)
    mem_free_percent = ((total_mem-free_mem)/total_mem)*100
    return round(mem_free_percent, 2)


def get_ambient_temperature(sensor_tag_collector):
    return sensor_tag_collector.get_temperature()[0]


def get_relative_humidity(sensor_tag_collector):
    return sensor_tag_collector.get_humidity()[1]


def get_pressure(sensor_tag_collector):
    # 1 millibar = 100 Pascal
    return sensor_tag_collector.get_barometer()[1] * 100


def get_battery_level(sensor_tag_collector):
    return sensor_tag_collector.get_battery_level()


def get_light_level(sensor_tag_collector):
    return sensor_tag_collector.get_light_level()


def get_vibration_level(sensor_tag_collector):
    # Accelerometer x,y,z in g
    x, y, z = sensor_tag_collector.get_accelerometer()
    # Magnitude of acceleration
    # ∣a⃗∣=√ (x*x+y*y+z*z)
    vib = int(math.sqrt((x*x + y*y + z*z)))
    return vib


def get_rpm(sensor_tag_collector):
    # RPM of Z-axis
    # Average of 5 samples
    _rpm_list = []
    while True:
        if len(_rpm_list) == 5:
            rpm = 0
            for _ in _rpm_list:
                rpm += _
            rpm = int(rpm / 5)
            break
        else:
            z_degree = sensor_tag_collector.get_gyroscope()[2]
            # (°/s to RPM)
            _rpm_list.append(int((abs(z_degree) * 0.16667)))
    return rpm


class PackageClass(LiotaPackage):
    def run(self, registry):
        import copy
        from liota.entities.metrics.metric import Metric
        from liota.entities.devices.sensor_tag import Sensors, SensorTagCollector

        # Acquire resources from registry
        iotcc_edge_system = copy.copy(registry.get("iotcc_edge_system"))
        iotcc = registry.get("iotcc")

        # Get values from configuration file
        config_path = registry.get("package_conf")
        config = {}
        execfile(config_path + '/sampleProp.conf', config)

        # Create metrics
        self.metrics = []
        # Operational metrics of EdgeSystem
        cpu_utilization_metric = Metric(
            name="CPU Utilization",
            unit=None,
            interval=10,
            aggregation_size=2,
            sampling_function=read_cpu_utilization
        )
        reg_cpu_utilization_metric = iotcc.register(cpu_utilization_metric)
        iotcc.create_relationship(iotcc_edge_system, reg_cpu_utilization_metric)
        # call to start collecting values from the device or system and sending to the data center component
        reg_cpu_utilization_metric.start_collecting()
        self.metrics.append(reg_cpu_utilization_metric)

        cpu_procs_metric = Metric(
            name="CPU Process",
            unit=None,
            interval=6,
            aggregation_size=8,
            sampling_function=read_cpu_procs
        )
        reg_cpu_procs_metric = iotcc.register(cpu_procs_metric)
        iotcc.create_relationship(iotcc_edge_system, reg_cpu_procs_metric)
        reg_cpu_procs_metric.start_collecting()
        self.metrics.append(reg_cpu_procs_metric)

        mem_free_metric = Metric(
            name="Memory Free",
            unit=None,
            interval=10,
            sampling_function=read_mem_free
        )
        reg_mem_free_metric = iotcc.register(mem_free_metric)
        iotcc.create_relationship(iotcc_edge_system, reg_mem_free_metric)
        reg_mem_free_metric.start_collecting()
        self.metrics.append(reg_mem_free_metric)

        # Connects to the SensorTag device over BLE
        self.sensor_tag_collector = SensorTagCollector(device_name=config['DeviceName'], device_mac=config['DeviceMac'],
                                                       sampling_interval_sec=5, retry_interval_sec=5,
                                                       sensors=[Sensors.TEMPERATURE, Sensors.HUMIDITY, Sensors.BAROMETER,
                                                                Sensors.BATTERY_LEVEL, Sensors.LIGHTMETER,
                                                                Sensors.ACCELEROMETER, Sensors.GYROSCOPE])
        sensor_tag = self.sensor_tag_collector.get_sensor_tag()
        # Registering SensorTagDevice with IoTCC
        reg_sensor_tag = iotcc.register(sensor_tag)
        iotcc.create_relationship(iotcc_edge_system, reg_sensor_tag)

        temperature_metric = Metric(
            name="AmbientTemperature",
            unit=ureg.degC,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_ambient_temperature(self.sensor_tag_collector)
        )
        reg_temperature_metric = iotcc.register(temperature_metric)
        iotcc.create_relationship(reg_sensor_tag, reg_temperature_metric)
        reg_temperature_metric.start_collecting()
        self.metrics.append(reg_temperature_metric)

        humidity_metric = Metric(
            name="RelativeHumidity",
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_relative_humidity(self.sensor_tag_collector)
        )
        reg_humidity_metric = iotcc.register(humidity_metric)
        iotcc.create_relationship(reg_sensor_tag, reg_humidity_metric)
        reg_humidity_metric.start_collecting()
        self.metrics.append(reg_humidity_metric)

        pressure_metric = Metric(
            name="Pressure",
            unit=ureg.Pa,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_pressure(self.sensor_tag_collector)
        )
        reg_pressure_metric = iotcc.register(pressure_metric)
        iotcc.create_relationship(reg_sensor_tag, reg_pressure_metric)
        reg_pressure_metric.start_collecting()
        self.metrics.append(reg_pressure_metric)

        battery_level_metric = Metric(
            name=str(config['DeviceName'])+'-BatteryLevel',
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_battery_level(self.sensor_tag_collector)
        )
        reg_battery_level_metric = iotcc.register(battery_level_metric)
        iotcc.create_relationship(reg_sensor_tag, reg_battery_level_metric)
        reg_battery_level_metric.start_collecting()
        self.metrics.append(reg_battery_level_metric)

        light_metric = Metric(
            name="LightLevel",
            unit=ureg.lx,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_light_level(self.sensor_tag_collector)
        )
        reg_light_metric = iotcc.register(light_metric)
        iotcc.create_relationship(reg_sensor_tag, reg_light_metric)
        reg_light_metric.start_collecting()
        self.metrics.append(reg_light_metric)

        vibration_metric = Metric(
            name="Vibration",
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_vibration_level(self.sensor_tag_collector)
        )
        reg_vibration_metric = iotcc.register(vibration_metric)
        iotcc.create_relationship(reg_sensor_tag, reg_vibration_metric)
        reg_vibration_metric.start_collecting()
        self.metrics.append(reg_vibration_metric)

        rpm_metric = Metric(
            name="RPM",
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_rpm(self.sensor_tag_collector)
        )
        reg_rpm_metric = iotcc.register(rpm_metric)
        iotcc.create_relationship(reg_sensor_tag, reg_rpm_metric)
        reg_rpm_metric.start_collecting()
        self.metrics.append(reg_rpm_metric)

    def clean_up(self):
        self.sensor_tag_collector.stop()
        for metric in self.metrics:
            metric.stop_collecting()

