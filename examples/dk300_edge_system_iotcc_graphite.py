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

from linux_metrics import cpu_stat, disk_stat, net_stat, mem_stat

from liota.dccs.iotcc import IotControlCenter
from liota.lib.utilities.identity import Identity
from liota.entities.devices.simulated_device import SimulatedDevice
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.dk300_edge_system import Dk300EdgeSystem
from liota.dcc_comms.websocket_dcc_comms import WebSocketDccComms
from liota.dccs.dcc import RegistrationFailure
from liota.dcc_comms.socket_comms import SocketDccComms
from liota.dccs.graphite import Graphite
from liota.lib.utilities.utility import get_default_network_interface, get_disk_name, read_user_config


# getting values from conf file
config = read_user_config('sampleProp.conf')

# Getting edge_system's network interface and disk name

# There are situations where route may not actually return a default route in the
# main routing table, as the default route might be kept in another table.
# Such cases should be handled manually.
network_interface = get_default_network_interface()
# If edge_system has multiple disks, only first disk will be returned.
# Such cases should be handled manually.
disk_name = get_disk_name()


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
    return cpu_stat.procs_running()
    

def read_cpu_utilization(sample_duration_sec=1):
    cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
    return round((100 - cpu_pcts['idle']), 2)


def read_swap_mem_free():
    total_swap = round(mem_stat.mem_stats()[4], 4)
    swap_mem_free = round(mem_stat.mem_stats()[5], 4)
    swap_free_percent = (swap_mem_free/total_swap)*100
    return round(swap_free_percent, 2)


def read_disk_usage_stats():
    return round(disk_stat.disk_reads_writes(disk_name)[0], 2)


def read_mem_free():
    total_mem = round(mem_stat.mem_stats()[1], 4)
    free_mem = round(mem_stat.mem_stats()[3], 4)
    mem_free_percent = ((total_mem-free_mem)/total_mem)*100
    return round(mem_free_percent, 2)
    

def read_network_packets_sent():
    # default network interface + loop_back
    packets_sent = net_stat.rx_tx_dump(network_interface)[1][1] + net_stat.rx_tx_dump('lo')[1][1]
    return packets_sent


def simulated_value():
    return random.randint(0, 20)


# ---------------------------------------------------------------------------
# In this example, we demonstrate how System health and some simluated data
# can be directed to two data center components (IoTCC and graphite) using Liota.
# The program illustrates the ease of use Liota brings to IoT application developers.

if __name__ == '__main__':

    # create a data center object, IoTCC in this case, using websocket as a transport layer
    # this object encapsulates the formats and protocols neccessary for the agent to interact with the dcc
    # UID/PASS login for now.
    identity = Identity(root_ca_cert=config['WebsocketCaCertFile'], username=config['IotCCUID'],
                        password=config['IotCCPassword'],
                        cert_file=config['ClientCertFile'], key_file=config['ClientKeyFile'])

    # Initialize DCC object with transport
    iotcc = IotControlCenter(
        WebSocketDccComms(url=config['WebSocketUrl'], verify_cert=config['VerifyServerCert'], identity=identity)
    )

    # create a System object encapsulating the particulars of a IoT System
    # argument is the name of this IoT System
    edge_system = Dk300EdgeSystem(config['EdgeSystemName'])

    try:

        # resister the IoT System with the IoTCC instance
        # this call creates a representation (a Resource) in IoTCC for this IoT System with the name given
        reg_edge_system = iotcc.register(edge_system)

        # these call set properties on the Resource representing the IoT System
        # properties are a key:value store
        reg_edge_system.set_properties(config['SystemPropList'])

        # ---------- Create metrics 'on' the Resource in IoTCC representing the IoT System
        # arguments:
        # local object referring to the Resource in IoTCC on which the metric should be associated
        # metric name
        # unit = An SI Unit (work needed here)
        # sampling_interval = the interval in seconds between called to the user function to obtain the next value for the metric
        # aggregation_size = the number of values collected in a cycle before publishing to DCC
        # value = user defined function to obtain the next value from the device associated with this metric
        cpu_utilization_metric = Metric(
            name="CPU Utilization",
            unit=None,
            interval=10,
            aggregation_size=2,
            sampling_function=read_cpu_utilization
        )
        reg_cpu_utilization_metric = iotcc.register(cpu_utilization_metric)
        iotcc.create_relationship(reg_edge_system, reg_cpu_utilization_metric)
        # call to start collecting values from the device or system and sending to the data center component
        reg_cpu_utilization_metric.start_collecting()

        cpu_procs_metric = Metric(
            name="CPU Process",
            unit=None,
            interval=6,
            aggregation_size=8,
            sampling_function=read_cpu_procs
        )
        reg_cpu_procs_metric = iotcc.register(cpu_procs_metric)
        iotcc.create_relationship(reg_edge_system, reg_cpu_procs_metric)
        reg_cpu_procs_metric.start_collecting()

        disk_usage_metric = Metric(
            name="Disk Usage Stats",
            unit=None,
            interval=6,
            aggregation_size=6,
            sampling_function=read_disk_usage_stats
        )
        reg_disk_usage_metric = iotcc.register(disk_usage_metric)
        iotcc.create_relationship(reg_edge_system, reg_disk_usage_metric)
        reg_disk_usage_metric.start_collecting()

        network_packets_sent_metric = Metric(
            name="Network Packets Sent",
            unit=None,
            interval=5,
            sampling_function=read_network_packets_sent
        )
        reg_network_packets_sent_metric = iotcc.register(network_packets_sent_metric)
        iotcc.create_relationship(reg_edge_system, reg_network_packets_sent_metric)
        reg_network_packets_sent_metric.start_collecting()

        # Here we are showing how to create a device object, registering it in IoTCC, and setting properties on it
        # Since there are no attached devices are as simulating one by considering RAM as separate from the IoT System
        # The agent makes possible many different data models
        # arguments:
        #        device name
        #        Read or Write
        #        another Resource in IoTCC of which the should be the child of a parent-child relationship among Resources
        ram_device = SimulatedDevice(config['DeviceName'], "Device-RAM")
        reg_ram_device = iotcc.register(ram_device)
        iotcc.create_relationship(reg_edge_system, reg_ram_device)

        # note that the location of this 'device' is different from the location of the IoTCC. It's not really different
        # but just an example of how one might create a device different from the IoTCC
        mem_free_metric = Metric(
            name="Memory Free",
            unit=None,
            interval=10,
            sampling_function=read_mem_free
        )
        reg_mem_free_metric = iotcc.register(mem_free_metric)
        iotcc.create_relationship(reg_ram_device, reg_mem_free_metric)
        reg_mem_free_metric.start_collecting()

        swap_mem_free_metric = Metric(
            name="Swap Memory Free",
            unit=None,
            interval=8,
            aggregation_size=5,
            sampling_function=read_swap_mem_free
        )
        reg_swap_mem_free_metric = iotcc.register(swap_mem_free_metric)
        iotcc.create_relationship(reg_ram_device, reg_swap_mem_free_metric)
        reg_swap_mem_free_metric.start_collecting()

    except RegistrationFailure:
        print "Registration to IOTCC failed"

    # Multiple DCC support
    # Sending data to an alternate data center component (e.g. data lake for analytics)
    # Graphite is a data center component
    # Socket is the transport which the agent uses to connect to the graphite instance
    graphite = Graphite(SocketDccComms(ip=config['GraphiteIP'],
                               port=config['GraphitePort']))
    graphite_reg_edge_system = graphite.register(edge_system)
    simulated_metric = Metric(
        name="edge.simulated.metric",
        unit=None,
        interval=10,
        aggregation_size=5,
        sampling_function=simulated_value
    )
    reg_simulated_metric = graphite.register(simulated_metric)
    graphite.create_relationship(graphite_reg_edge_system, reg_simulated_metric)
    reg_simulated_metric.start_collecting()
