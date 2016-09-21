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
import psutil

dependencies = ["graphite"]

#---------------------------------------------------------------------------
# User defined methods

def read_cpu_procs():
    cnt = 0
    procs = psutil.pids()
    for i in procs[:]:
        p = psutil.Process(i)
        if p.status() == 'running':
            cnt += 1
    return cnt

def read_cpu_utilization(sample_duration_sec=1):
    return round(psutil.cpu_percent(interval=sample_duration_sec), 2)

def read_disk_busy_stats():
    return round(psutil.disk_usage('/dev/disk1')[3], 2)

def read_network_bits_received():
    return round((psutil.net_io_counters(pernic=True)["en0"][1] * 8) / (8192), 2)

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
        metric_name = "CPU.Utilization"
        metric1 = Metric(name=metric_name, parent=system,
                entity_id=metric_name,
                unit=None, interval=5,
                aggregation_size=1,
                sampling_function=read_cpu_utilization
            )
        reg_metric1 = graphite.register_metric(metric1)
        reg_metric1.start_collecting()
        self.metrics.append(reg_metric1)
        
        metric_name = "CPU.Process"
        metric2 = Metric(name=metric_name, parent=system,
                entity_id=metric_name,
                unit=None, interval=5,
                aggregation_size=1,
                sampling_function=read_cpu_procs
            )
        reg_metric2 = graphite.register_metric(metric2)
        reg_metric2.start_collecting()
        self.metrics.append(reg_metric2)
        
        metric_name = "Disk.BusyStats"
        metric3 = Metric(name=metric_name, parent=system,
                entity_id=metric_name,
                unit=None, interval=5,
                aggregation_size=1,
                sampling_function=read_disk_busy_stats
            )
        reg_metric3 = graphite.register_metric(metric3)
        reg_metric3.start_collecting()
        self.metrics.append(reg_metric3)
        
        metric_name = "Network.BitsReceived"
        metric4 = Metric(name=metric_name, parent=system,
                entity_id=metric_name,
                unit=None, interval=5,
                aggregation_size=1,
                sampling_function=read_network_bits_received
            )
        reg_metric4 = graphite.register_metric(metric4)
        reg_metric4.start_collecting()
        self.metrics.append(reg_metric4)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()
