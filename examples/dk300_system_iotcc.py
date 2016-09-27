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
from liota.dccs.iotcc import IotControlCenter
from liota.entities.devices.simulated_device import SimulatedDevice
from liota.entities.metrics.metric import Metric
from liota.entities.systems.dk300_system import Dk300System
from liota.dcc_comms.websocket_dcc_comms import WebSocketDccComms

# getting values from conf file
config = {}
execfile('samplePropIotcc.conf', config)


# some standard metrics for Linux systems
# agent classes for different IoT system
# agent classes for different data center components
# agent classes for different kinds of of devices, connected to the IoT System
# we are showing here how to create a representation for a Device in IoTCC but
# using the notion of RAM (because we have no connected devices yet)
# agent classes for different kinds of layer 4/5 connections from agent to DCC
# -------User defined functions for getting the next value for a metric --------
# usage of these shown below in main
# semantics are that on each call the function returns the next available value
# from the device or system associated to the metric.

def read_cpu_procs():
    procs_running = 0
    for p in psutil.process_iter():
        procs_running += 1
    return procs_running


def read_cpu_utilization(sample_duration_sec=1):
    return round(psutil.cpu_percent(sample_duration_sec), 2)


def read_swap_mem_free():
    return round((100 - psutil.swap_memory().percent), 2)


def read_disk_usage_stats():
    return round(psutil.disk_usage('/').percent, 2)


def read_mem_free():
    return round((100 - psutil.virtual_memory().percent), 2)


def read_network_bits_recieved():
    return int(psutil.net_io_counters(pernic=False).packets_sent)


def simulated_device():
    return random.randint(0, 20)


#---------------------------------------------------------------------------
# In this example, we demonstrate how System health and some simluated data
# can be directed to two data center components (IoTCC and graphite) using Liota.
# The program illustrates the ease of use Liota brings to IoT application developers.

if __name__ == '__main__':


    # create a data center object, IoTCC in this case, using websocket as a transport layer
    # this object encapsulates the formats and protocols neccessary for the agent to interact with the dcc
    # UID/PASS login for now.
    iotcc = IotControlCenter(config['IotCCUID'], config['IotCCPassword'], WebSocketDccComms(url=config['WebSocketUrl']))

    # create a System object encapsulating the particulars of a IoT System
    # argument is the name of this IoT System
    system = Dk300System(config['SystemName'])

    # resister the IoT System with the IoTCC instance
    # this call creates a representation (a Resource) in IoTCC for this IoT System with the name given
    reg_system = iotcc.register(system)

    # these call set properties on the Resource representing the IoT System
    # properties are a key:value store
    reg_system.set_properties(config['SystemPropList'])

    # ---------- Create metrics 'on' the Resource in IoTCC representing the IoT System
    # arguments:
    # local object referring to the Resource in IoTCC on which the metric should be associated
    # metric name
    # unit = An SI Unit (work needed here)
    # sampling_interval = the interval in seconds between called to the user function to obtain the next value for the metric
    # aggregation_size = the number of values collected in a cycle before publishing to DCC
    # value = user defined function to obtain the next value from the device associated with this metric
    cpu_utilization_metric = Metric(
        name="CPU_Utilization",
        parent=system,
        unit=None,
        interval=10,
        aggregation_size=2,
        sampling_function=read_cpu_utilization
    )
    reg_cpu_utilization_metric = iotcc.register(cpu_utilization_metric)

    # call to start collecting values from the device or system and sending to the data center component
    reg_cpu_utilization_metric.start_collecting()

    cpu_procs_metric = Metric(
        name="CPU_Process",
        parent=system,
        unit=None,
        interval=6,
        aggregation_size=8,
        sampling_function=read_cpu_procs
    )
    reg_cpu_procs_metric = iotcc.register(cpu_procs_metric)
    reg_cpu_procs_metric.start_collecting()

    disk_usage_metric = Metric(
        name="Disk_Usage_Stats",
        parent=system,
        unit=None,
        aggregation_size=6,
        sampling_function=read_disk_usage_stats
    )
    reg_disk_usage_metric = iotcc.register(disk_usage_metric)
    reg_disk_usage_metric.start_collecting()

    network_bits_received_metric = Metric(
        name="Network_Bits_Received",
        parent=system,
        unit=None,
        interval=5,
        sampling_function=read_network_bits_recieved
    )
    reg_network_bits_received_metric = iotcc.register(network_bits_received_metric)
    reg_network_bits_received_metric.start_collecting()

    # Here we are showing how to create a device object, registering it in IoTCC, and setting properties on it
    # Since there are no attached devices are as simulating one by considering RAM as separate from the IoT System
    # The agent makes possible many different data models
    # arguments:
    #        device name
    #        Read or Write
    #        another Resource in IoTCC of which the should be the child of a parent-child relationship among Resources
    ram_device = SimulatedDevice(config['DeviceName'], system, "Device-RAM")
    reg_ram_device = iotcc.register(ram_device)
    # note that the location of this 'device' is different from the location of the IoTCC. It's not really different
    # but just an example of how one might create a device different from the IoTCC
    mem_free_metric = Metric(
        name="Memory_Free",
        parent=ram_device,
        unit=None,
        interval=10,
        sampling_function=read_mem_free
    )
    reg_mem_free_metric = iotcc.register(mem_free_metric)
    reg_mem_free_metric.start_collecting()

    swap_mem_free_metric = Metric(
        name="Swap_Memory_Free",
        parent=ram_device,
        unit=None,
        interval=8,
        aggregation_size=5,
        sampling_function=read_swap_mem_free
    )
    reg_swap_mem_free_metric = iotcc.register(swap_mem_free_metric)
    reg_swap_mem_free_metric.start_collecting()
