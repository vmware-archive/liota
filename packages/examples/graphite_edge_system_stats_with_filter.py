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

from linux_metrics import cpu_stat, disk_stat, net_stat

from liota.core.package_manager import LiotaPackage
from liota.lib.utilities.filters.range_filter import RangeFilter, Type
from liota.lib.utilities.filters.windowing_scheme.windowing_scheme import WindowingScheme

dependencies = ["graphite"]

# Filters to filter data at Sampling Functions
# Simple filters
cpu_pro_filter = RangeFilter(Type.CLOSED_REJECT, 5, 10)  # If no of CPU processes <=5 or >=10
cpu_util_filter = RangeFilter(Type.AT_LEAST, None, 85)  # CPU util >= 85
disk_usage_filter = RangeFilter(Type.AT_LEAST, None, 80)  # Disk usage >= 80%
net_usage_filter = RangeFilter(Type.AT_LEAST, None, 1000000)  # Network usage >= 1Mb

# Filter with windowing scheme
cpu_util_filter_with_window = WindowingScheme(cpu_util_filter, 30)


# ---------------------------------------------------------------------------
# User defined methods with RangeFilters

def read_cpu_procs():
    cnt = cpu_stat.procs_running()
    return cpu_pro_filter.filter(cnt)


def read_cpu_utilization(sample_duration_sec=1):
    cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
    return cpu_util_filter_with_window.filter(round((100 - cpu_pcts['idle']), 2))


def read_disk_usage_stats():
    return disk_usage_filter.filter(round(disk_stat.disk_reads_writes('sda')[0], 2))


def read_network_bytes_received():
    return net_usage_filter.filter(round(net_stat.rx_tx_bytes('ens33')[0], 2))


class PackageClass(LiotaPackage):
    def run(self, registry):
        import copy
        from liota.entities.metrics.metric import Metric

        # Acquire resources from registry
        edge_system = copy.copy(registry.get("edge_system"))
        graphite = registry.get("graphite")
        reg_edge_system = graphite.register(edge_system)

        # Get values from configuration file
        config_path = registry.get("package_conf")
        config = {}
        execfile(config_path + '/sampleProp.conf', config)

        # Create metrics
        self.metrics = []
        metric_name = "EdgeSystem.CPU_Utilization"
        metric_cpu_utilization = Metric(name=metric_name,
                                        unit=None, interval=5,
                                        aggregation_size=1,
                                        sampling_function=read_cpu_utilization
                                        )
        reg_metric_cpu_utilization = graphite.register(metric_cpu_utilization)
        graphite.create_relationship(reg_edge_system, reg_metric_cpu_utilization)
        reg_metric_cpu_utilization.start_collecting()
        self.metrics.append(reg_metric_cpu_utilization)

        metric_name = "EdgeSystem.CPU_Process"
        metric_cpu_procs = Metric(name=metric_name,
                                  unit=None, interval=5,
                                  aggregation_size=1,
                                  sampling_function=read_cpu_procs
                                  )
        reg_metric_cpu_procs = graphite.register(metric_cpu_procs)
        graphite.create_relationship(reg_edge_system, reg_metric_cpu_procs)
        reg_metric_cpu_procs.start_collecting()
        self.metrics.append(reg_metric_cpu_procs)

        metric_name = "EdgeSystem.Disk_Busy_Stats"
        metric_disk_busy_stats = Metric(name=metric_name,
                                        unit=None, interval=5,
                                        aggregation_size=1,
                                        sampling_function=read_disk_usage_stats
                                        )
        reg_metric_disk_busy_stats = graphite.register(metric_disk_busy_stats)
        graphite.create_relationship(reg_edge_system, reg_metric_disk_busy_stats)
        reg_metric_disk_busy_stats.start_collecting()
        self.metrics.append(reg_metric_disk_busy_stats)

        metric_name = "EdgeSystem.Network_Bytes_Received"
        metric_network_bytes_received = Metric(name=metric_name,
                                               unit=None, interval=5,
                                               aggregation_size=1,
                                               sampling_function=read_network_bytes_received
                                               )
        reg_metric_network_bytes_received = graphite.register(metric_network_bytes_received)
        graphite.create_relationship(reg_edge_system, reg_metric_network_bytes_received)
        reg_metric_network_bytes_received.start_collecting()
        self.metrics.append(reg_metric_network_bytes_received)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()

