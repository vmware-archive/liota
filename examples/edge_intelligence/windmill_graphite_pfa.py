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

# This example depicts how edge component can be used to take actions locally based on pfa model
# and actions can then be send to device using actuator_udm method defined here, which is currently just printing
# the returned value is from PFAComponent as actions. Only the gateway metrics are being published to Graphite DCC.

import pint
import math
import Queue

from linux_metrics import cpu_stat, mem_stat

from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.devices.sensor_tag import Sensors, SensorTagCollector
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
from liota.dcc_comms.socket_comms import SocketDccComms
from liota.dccs.dcc import RegistrationFailure
from liota.edge_component.pfa_component import PFAComponent

# getting values from conf file
config = {}
execfile('../sampleProp.conf', config)

# create a pint unit registry
ureg = pint.UnitRegistry()

rpm_model_queue = Queue.Queue()

def read_cpu_procs():
    return cpu_stat.procs_running()


def read_cpu_utilization(sample_duration_sec=1):
    cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
    return round((100 - cpu_pcts['idle']), 2)


def read_mem_free():
    total_mem = round(mem_stat.mem_stats()[1], 4)
    free_mem = round(mem_stat.mem_stats()[3], 4)
    mem_free_percent = ((total_mem - free_mem) / total_mem) * 100
    return round(mem_free_percent, 2)


def get_ambient_temperature(sensor_tag_collector):
    return sensor_tag_collector.get_temperature()[0]


def get_relative_humidity(sensor_tag_collector):
    return sensor_tag_collector.get_humidity()[1]


def get_pressure(sensor_tag_collector):
    # 1 millibar = 100 Pascal
    return sensor_tag_collector.get_barometer()[1] * 100


def get_light_level(sensor_tag_collector):
    return sensor_tag_collector.get_light_level()


def get_vibration_level(sensor_tag_collector):
    # Accelerometer x,y,z in g
    x, y, z = sensor_tag_collector.get_accelerometer()
    # Magnitude of acceleration
    # ∣a⃗∣=√ (x*x+y*y+z*z)
    vib = math.sqrt((x * x + y * y + z * z))
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
    rpm_model_queue.put(rpm)
    return rpm

# we keep metric in queue and get one by one from the queue
def get_rpm_for_model():
    return rpm_model_queue.get(block=True)

# actuator_udm can be used to pass on the value to the actuator, as of now we are printing them
def actuator_udm(value):
    print value


# ---------------------------------------------------------------------------------------
# In this example, we demonstrate how metrics collected from a SensorTag device over BLE
# can be directed to graphite data center component using Liota.
# The program illustrates the ease of use Liota brings to IoT application developers.

if __name__ == '__main__':

    # create a data center object, graphite in this case, using websocket as a transport layer
    graphite = Graphite(SocketDccComms(ip=config['GraphiteIP'],
                                       port=config['GraphitePort']))

    try:
        # create a System object encapsulating the particulars of a IoT System
        # argument is the name of this IoT System
        edge_system = Dell5KEdgeSystem(config['EdgeSystemName'])

        # resister the IoT System with the graphite instance
        # this call creates a representation (a Resource) in graphite for this IoT System with the name given
        reg_edge_system = graphite.register(edge_system)

        # Operational metrics of EdgeSystem
        cpu_utilization_metric = Metric(
            name="windmill.CPU_Utilization",
            unit=None,
            interval=10,
            aggregation_size=2,
            sampling_function=read_cpu_utilization
        )
        reg_cpu_utilization_metric = graphite.register(cpu_utilization_metric)
        graphite.create_relationship(reg_edge_system, reg_cpu_utilization_metric)
        # call to start collecting values from the device or system and sending to the data center component
        reg_cpu_utilization_metric.start_collecting()

        cpu_procs_metric = Metric(
            name="windmill.CPU_Process",
            unit=None,
            interval=6,
            aggregation_size=8,
            sampling_function=read_cpu_procs
        )
        reg_cpu_procs_metric = graphite.register(cpu_procs_metric)
        graphite.create_relationship(reg_edge_system, reg_cpu_procs_metric)
        reg_cpu_procs_metric.start_collecting()

        mem_free_metric = Metric(
            name="windmill.Memory_Free",
            unit=None,
            interval=10,
            sampling_function=read_mem_free
        )
        reg_mem_free_metric = graphite.register(mem_free_metric)
        graphite.create_relationship(reg_edge_system, reg_mem_free_metric)
        reg_mem_free_metric.start_collecting()

        # Connects to the SensorTag device over BLE
        sensor_tag_collector = SensorTagCollector(device_name=config['DeviceName'], device_mac=config['DeviceMac'],
                                                  sampling_interval_sec=1, retry_interval_sec=5,
                                                  sensors=[Sensors.TEMPERATURE, Sensors.HUMIDITY, Sensors.BAROMETER,
                                                           Sensors.LIGHTMETER,
                                                           Sensors.ACCELEROMETER, Sensors.GYROSCOPE])
        sensor_tag = sensor_tag_collector.get_sensor_tag()
        # Registering SensorTagDevice with graphite
        reg_sensor_tag = graphite.register(sensor_tag)
        graphite.create_relationship(reg_edge_system, reg_sensor_tag)

        temperature_metric = Metric(
            name="windmill.AmbientTemperature",
            unit=ureg.degC,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_ambient_temperature(sensor_tag_collector)
        )
        reg_temperature_metric = graphite.register(temperature_metric)
        graphite.create_relationship(reg_sensor_tag, reg_temperature_metric)
        reg_temperature_metric.start_collecting()

        humidity_metric = Metric(
            name="windmill.RelativeHumidity",
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_relative_humidity(sensor_tag_collector)
        )
        reg_humidity_metric = graphite.register(humidity_metric)
        graphite.create_relationship(reg_sensor_tag, reg_humidity_metric)
        reg_humidity_metric.start_collecting()

        pressure_metric = Metric(
            name="windmill.Pressure",
            unit=ureg.Pa,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_pressure(sensor_tag_collector)
        )
        reg_pressure_metric = graphite.register(pressure_metric)
        graphite.create_relationship(reg_sensor_tag, reg_pressure_metric)
        reg_pressure_metric.start_collecting()

        light_metric = Metric(
            name="windmill.LightLevel",
            unit=ureg.lx,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_light_level(sensor_tag_collector)
        )
        reg_light_metric = graphite.register(light_metric)
        graphite.create_relationship(reg_sensor_tag, reg_light_metric)
        reg_light_metric.start_collecting()

        vibration_metric = Metric(
            name="windmill.Vibration",
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_vibration_level(sensor_tag_collector)
        )
        reg_vibration_metric = graphite.register(vibration_metric)
        graphite.create_relationship(reg_sensor_tag, reg_vibration_metric)
        reg_vibration_metric.start_collecting()

        rpm_metric = Metric(
            name="windmill.RPM",
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=lambda: get_rpm(sensor_tag_collector)
        )
        reg_rpm_metric = graphite.register(rpm_metric)
        graphite.create_relationship(reg_sensor_tag, reg_rpm_metric)
        reg_rpm_metric.start_collecting()
        pfa_rpm_metric = Metric(
            name="windmill.RPM",
            unit=None,
            interval=0,
            aggregation_size=1,
            sampling_function=get_rpm_for_model
        )
        # ModelPath can be edited in the sampleProp.conf file
        # pass value to actuator as of now the actuator_udm prints the value on the console
        # PFA edge component is a part of edge intelligence and analytics for Liota, uses pfa model for analytics.

        edge_component = PFAComponent(config['ModelPath'],
            actuator_udm=actuator_udm)

        pfa_reg_rpm_metric = edge_component.register(pfa_rpm_metric)
        pfa_reg_rpm_metric.start_collecting()

    except RegistrationFailure:
        print "Registration to graphite failed"
        sensor_tag_collector.stop()
