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

from liota.core.package_manager import LiotaPackage

dependencies = ["vrops"]

#---------------------------------------------------------------------------
# User defined methods

def read_cpu_procs():
    from linux_metrics import cpu_stat

    return cpu_stat.procs_running()

def read_cpu_utilization(sample_duration_sec=1):
    from linux_metrics import cpu_stat

    cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
    return round((100 - cpu_pcts['idle']), 2)

def read_disk_busy_stats(sample_duration_sec=1):
    from linux_metrics import disk_stat

    return round(disk_stat.disk_busy('sda', sample_duration_sec), 4)

def read_network_bits_recieved():
    from linux_metrics import net_stat

    return round((net_stat.rx_tx_bits('eth0')[0]) / (8192), 2)

class PackageClass(LiotaPackage):

    def run(self, registry):
        # Acquire resources from registry
        vrops = registry.get("vrops")
        vrops_gateway = registry.get("vrops_gateway")
        assert(vrops_gateway.registered)

        # Create metrics
        self.metrics = []
        cpu_utilization = vrops.create_metric(
                vrops_gateway, "CPU Utilization",
                unit=None,
                aggregation_size=2,
                sampling_interval_sec=5,
                sampling_function=read_cpu_utilization
            )
        cpu_utilization.start_collecting()
        self.metrics.append(cpu_utilization)

        cpu_procs = vrops.create_metric(
                vrops_gateway, "CPU Process",
                unit=None,
                sampling_interval_sec=10,
                sampling_function=read_cpu_procs
            )
        cpu_procs.start_collecting()
        self.metrics.append(cpu_procs)

        disk_busy_stats = vrops.create_metric(
                vrops_gateway, "Disk Busy Stats",
                unit=None,
                aggregation_size=6,
                sampling_function=read_disk_busy_stats
            )
        disk_busy_stats.start_collecting()
        self.metrics.append(disk_busy_stats)

        network_bits_recieved = vrops.create_metric(
                vrops_gateway, "Network Bits Recieved",
                unit=None,
                aggregation_size=1,
                sampling_interval_sec=30,
                sampling_function=read_network_bits_recieved
            )
        network_bits_recieved.start_collecting()
        self.metrics.append(network_bits_recieved)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()
