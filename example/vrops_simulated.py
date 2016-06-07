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

from linux_metrics import cpu_stat, disk_stat, net_stat, mem_stat
from liota.boards.gateway_dk300 import Dk300
from liota.dcc.vrops import Vrops
from liota.things.ram import RAM
from liota.transports.web_socket import WebSocket
import random

# getting values from conf file
config = {}
execfile('sampleProp.conf', config)

# some standard metrics for Linux systems
# agent classes for different IoT gateways
# agent classes for different data center components
# agent classes for different kinds of of devices, 'Things', connected to the gw
# we are showing here how to create a representation for a Thing in vROps but
# using the notion of RAM (because we have no connected devies yet)
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

def read_disk_busy_stats(sample_duration_sec=1):
    return round(disk_stat.disk_busy('sda', sample_duration_sec), 4)

def read_mem_free():
    return round((mem_stat.mem_stats()[3]) / (1048576), 3)

def read_network_bits_recieved():
    return round((net_stat.rx_tx_bits('eth0')[0]) / (8192), 2)

def simulated_device():
    return random.randint(0, 20)

#---------------------------------------------------------------------------
# In this example, we demonstrate how gateway health and some simluated data 
# can be directed to vrops, VMware's data center component using Liota.
# The program illustrates the ease of use Liota brings to IoT application developers.

if __name__ == '__main__':

    # create a data center object, vROps in this case, using websocket as a transport layer
    # this object encapsulates the formats and protocols neccessary for the agent to interact with the dcc
    # UID/PASS login for now.
    vrops = Vrops(config['vROpsUID'], config['vROpsPass'], WebSocket(url=config['WebSocketUrl']))

    # create a gateway object encapsulating the particulars of a gateway/board
    # argument is the name of this gateway
    gateway = Dk300(config['Gateway1Name'])

    # resister the gateway with the vrops instance
    # this call creates a representation (a Resource) in vrops for this gateway with the name given
    vrops_gateway = vrops.register(gateway)

    if vrops_gateway.registered:
        # these call set properties on the Resource representing the gateway in the vrops instance
        # properties are a key:value store
        # arguments are (key, value)
        for item in config['Gateway1PropList']:
            for key, value in item.items():
                vrops.set_properties(key, value, vrops_gateway)
        # ---------- Create metrics 'on' the Resource in vrops representing the gateway
        # arguments:
        #          local object referring to the Resource in vrops on which the metric should be associated
        #          metric name
        #          unit = An SI Unit (work needed here)
        #          sampling_interval = the interval in seconds between called to the user function to obtain the next value for the metric
        #          report_interfal = the interval between subsequent sends to the data center component. If sample > report values are queued
        #          value = user defined function to obtain the next value from the device associated with this metric
        cpu_utilization = vrops.create_metric(vrops_gateway, "CPU_Utilization", unit=None, sampling_interval_sec=50, aggregation_size=2, sampling_function=read_cpu_utilization)

        # call to start collecting values from the device or system and sending to the data center component
        cpu_utilization.start_collecting()

        cpu_procs = vrops.create_metric(vrops_gateway, "CPU_Process", unit=None, sampling_interval_sec=6, sampling_function=read_cpu_procs)
        cpu_procs.start_collecting()

        disk_busy_stats = vrops.create_metric(vrops_gateway, "Disk_Busy_Stats", unit=None, aggregation_size=6, sampling_function=read_disk_busy_stats)
        disk_busy_stats.start_collecting()

        network_bits_recieved = vrops.create_metric(vrops_gateway, "Network_Bits_Recieved", unit=None, sampling_interval_sec=5, sampling_function=read_network_bits_recieved)
        network_bits_recieved.start_collecting()
    else:
        print "vROPS resource not registered successfully"

    # Here we are showing how to create a device object, registering it in vrops, and setting properties on it
    # Since there are no attached devices are as simulating one by considering RAM as separate from the gateway
    # The agent makes possible many different data models
    # arguments:
    #        device name
    #        Read or Write
    #        another Resource in vrops of which the should be the child of a parent-child relationship among Resources
    ram = RAM(config['Device1Name'], 'Read', gateway)
    vrops_device = vrops.register(ram)
    # note that the location of this 'device' is different from the location of the gateway. It's not really different
    # but just an example of how one might create a device different from the gateway
    if vrops_device.registered:
        for item in config['Device1PropList']:
            for key, value in item.items():
                vrops.set_properties(key, value, vrops_device)
        mem_free = vrops.create_metric(vrops_device, "Memory_Free", unit=None, sampling_interval_sec=10, sampling_function=read_mem_free)
        mem_free.start_collecting()
    else:
        print "vROPS resource not registered successfully"

