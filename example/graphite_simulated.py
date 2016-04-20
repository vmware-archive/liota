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
from liota.boards import gateway
from liota.boards.gateway_dk300 import Dk300
from liota.dcc.graphite_dcc import Graphite
from liota.dcc.vrops import Vrops
from liota.things.ram import RAM
from liota.transports.socket_connection import Socket
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





if __name__ == '__main__':


    # Sending data to an alternate data center component (e.g. data lake for analytics)
    # Graphite is a data center component
    # Socket is the transport which the agent uses to connect to the graphite instance
    graphite = Graphite(Socket(sampleProp.GraphiteIP, sampleProp.GraphitePort))
    content_metric = graphite.create_metric(gateway, sampleProp.GraphiteMetric, sampling_interval_sec=15, aggregation_size=1, sampling_function=simulated_device)
    content_metric.start_collecting()
