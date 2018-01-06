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
from liota.lib.utilities.utility import get_default_network_interface, get_disk_name
from linux_metrics import mem_stat
import logging

log = logging.getLogger(__name__)

dependencies = ["iotcc_mqtt"]

# Getting edge_system's network interface and disk name

# There are situations where route may not actually return a default route in the
# main routing table, as the default route might be kept in another table.
# Such cases should be handled manually.
network_interface = get_default_network_interface()
# If edge_system has multiple disks, only first disk will be returned.
# Such cases should be handled manually.
disk_name = get_disk_name()


# ---------------------------------------------------------------------------
# This is a sample application package to publish edge system stats data to
# IoTCC using MQTT protocol as DCC Comms
# User defined methods


def read_cpu_procs():
    """
    User defined method
    :return: number of running cpu processes.
    """
    return cpu_stat.procs_running()


def read_cpu_utilization(sample_duration_sec=1):
    """
    User defined method
    :param sample_duration_sec: Sample duration sample
    is collected
    :return: percentage of cpu utilized.
    """
    cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
    return round((100 - cpu_pcts['idle']), 2)


def read_disk_usage_stats():
    """
    User defined method
    :return: disk usage.
    """
    # If the device raises an intermittent exception during metric collection process it will be required
    # to be handled in the user code otherwise if an exception is thrown from user code
    # the collection process will be stopped for that metric.
    # If the None value is returned by UDM then metric value for that particular collector instance won't be published.
    try:
        disk_stat_value = round(disk_stat.disk_reads_writes(disk_name)[0], 2)
    except Exception:
        return None
    return disk_stat_value


def read_network_bytes_received():
    """
    User defined method.
    :return: network bytes received
    """
    return round(net_stat.rx_tx_bytes(network_interface)[0], 2)


def read_mem_free():
    """
    User defined method.
    :return: percentage of memory free.
    """
    total_mem = round(mem_stat.mem_stats()[1], 4)
    free_mem = round(mem_stat.mem_stats()[3], 4)
    mem_free_percent = ((total_mem - free_mem) / total_mem) * 100
    return round(mem_free_percent, 2)


class PackageClass(LiotaPackage):
    def run(self, registry):
        """
        The execution function of a liota package.

        Acquires "iotcc_mqtt" and "iotcc_mqtt_edge_system" from registry and registers edge_system related metrics
        with the DCC and publishes those metrics.

        :param registry: the instance of ResourceRegistryPerPackage of the package
        :return:
        """
        import copy
        from liota.entities.metrics.metric import Metric

        # Acquire resources from registry
        iotcc_edge_system = copy.copy(registry.get("iotcc_mqtt_edge_system"))
        iotcc = registry.get("iotcc_mqtt")

        try:
            # Create metrics
            self.metrics = []
            metric_name = "CPU Utilization"
            metric_cpu_utilization = Metric(name=metric_name,
                                            unit=None, interval=5,
                                            aggregation_size=1,
                                            sampling_function=read_cpu_utilization
                                            )
            reg_metric_cpu_utilization = iotcc.register(metric_cpu_utilization)
            iotcc.create_relationship(iotcc_edge_system, reg_metric_cpu_utilization)
            reg_metric_cpu_utilization.start_collecting()
            self.metrics.append(reg_metric_cpu_utilization)

            metric_name = "CPU Process"
            metric_cpu_procs = Metric(name=metric_name,
                                      unit=None, interval=5,
                                      aggregation_size=1,
                                      sampling_function=read_cpu_procs
                                      )
            reg_metric_cpu_procs = iotcc.register(metric_cpu_procs)
            iotcc.create_relationship(iotcc_edge_system, reg_metric_cpu_procs)
            reg_metric_cpu_procs.start_collecting()
            self.metrics.append(reg_metric_cpu_procs)

            metric_name = "Disk Usage Stats"
            metric_disk_usage_stats = Metric(name=metric_name,
                                             unit=None, interval=5,
                                             aggregation_size=1,
                                             sampling_function=read_disk_usage_stats
                                             )
            reg_metric_disk_usage_stats = iotcc.register(metric_disk_usage_stats)
            iotcc.create_relationship(iotcc_edge_system, reg_metric_disk_usage_stats)
            reg_metric_disk_usage_stats.start_collecting()
            self.metrics.append(reg_metric_disk_usage_stats)

            metric_name = "Network Bytes Received"
            metric_network_bytes_received = Metric(name=metric_name,
                                                   unit=None, interval=5,
                                                   aggregation_size=1,
                                                   sampling_function=read_network_bytes_received
                                                   )
            reg_metric_network_bytes_received = iotcc.register(metric_network_bytes_received)
            iotcc.create_relationship(iotcc_edge_system, reg_metric_network_bytes_received)
            reg_metric_network_bytes_received.start_collecting()
            self.metrics.append(reg_metric_network_bytes_received)

            metric_name = "Memory Free"
            mem_free_metric = Metric(name=metric_name,
                                     unit=None, interval=10,
                                     aggregation_size=1,
                                     sampling_function=read_mem_free
                                     )
            reg_mem_free_metric = iotcc.register(mem_free_metric)
            iotcc.create_relationship(iotcc_edge_system, reg_mem_free_metric)
            reg_mem_free_metric.start_collecting()
            self.metrics.append(reg_mem_free_metric)
        except Exception as e:
            log.error(
                'Exception while loading metric {0} for Edge System {1} - {2}'.format(metric_name,
                                                                                      iotcc_edge_system.ref_entity.name,
                                                                                      str(e)))

    def clean_up(self):
        """
        The clean up function of a liota package.

        Stops metric collection and publish.
        :return:
        """
        # Kindly include this call to stop the metrics collection on package unload
        for metric in self.metrics:
            metric.stop_collecting()
