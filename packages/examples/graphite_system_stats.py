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
import random

dependencies = ["graphite"]

#---------------------------------------------------------------------------
# User defined methods
def simulated_sampling_function():
    return random.randint(0, 20)
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

def read_network_bits_received():
    from linux_metrics import net_stat

    return round((net_stat.rx_tx_bits('eth0')[0]) / (8192), 2)

class PackageClass(LiotaPackage):

    def run(self, registry):
        import ConfigParser, copy
        from liota.entities.metrics.metric import Metric
        
        # Acquire resources from registry
        system = copy.copy(registry.get("system"))
        graphite = registry.get("graphite")

        # Get values from configuration file
        config_path = registry.get("package_conf")
        config = ConfigParser.ConfigParser()
        config.readfp(open(config_path + "/sampleProp.conf"))

        # Create metrics
        self.metrics = []
        metric_name = config.get('DEFAULT', 'Metric1Name')
        metric1 = Metric(name=metric_name, parent=system,
                entity_id=metric_name,
                unit=None, interval=5,
                aggregation_size=1,
                #sampling_function=read_cpu_utilization
                sampling_function=simulated_sampling_function
            )
        reg_metric1 = graphite.register_metric(metric1)
        reg_metric1.start_collecting()
        self.metrics.append(reg_metric1)
        
        metric_name = config.get('DEFAULT', 'Metric2Name')
        metric2 = Metric(name=metric_name, parent=system,
                entity_id=metric_name,
                unit=None, interval=5,
                aggregation_size=1,
                #sampling_function=read_cpu_utilization
                sampling_function=simulated_sampling_function
            )
        reg_metric2 = graphite.register_metric(metric2)
        reg_metric2.start_collecting()
        self.metrics.append(reg_metric2)
        
        metric_name = config.get('DEFAULT', 'Metric3Name')
        metric3 = Metric(name=metric_name, parent=system,
                entity_id=metric_name,
                unit=None, interval=5,
                aggregation_size=1,
                #sampling_function=read_cpu_utilization
                sampling_function=simulated_sampling_function
            )
        reg_metric3 = graphite.register_metric(metric3)
        reg_metric3.start_collecting()
        self.metrics.append(reg_metric3)
        
        metric_name = config.get('DEFAULT', 'Metric4Name')
        metric4 = Metric(name=metric_name, parent=system,
                entity_id=metric_name,
                unit=None, interval=5,
                aggregation_size=1,
                #sampling_function=read_cpu_utilization
                sampling_function=simulated_sampling_function
            )
        reg_metric4 = graphite.register_metric(metric4)
        reg_metric4.start_collecting()
        self.metrics.append(reg_metric4)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()
