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
from linux_metrics import mem_stat
from liota.lib.utilities.utility import read_user_config

dependencies = ["iotcc"]

def read_mem_free():
    total_mem = round(mem_stat.mem_stats()[1],4)
    free_mem = round(mem_stat.mem_stats()[3],4)
    mem_free_percent = ((total_mem-free_mem)/total_mem)*100
    return round(mem_free_percent, 2)
    

class PackageClass(LiotaPackage):

    def run(self, registry):
        from liota.entities.devices.simulated_device import SimulatedDevice
        from liota.entities.metrics.metric import Metric
        import copy

        # Acquire resources from registry
        self.iotcc = registry.get("iotcc")
        # Creating a copy of edge_system object to keep original object "clean"
        self.iotcc_edge_system = copy.copy(registry.get("iotcc_edge_system"))

        # Get values from configuration file
        config_path = registry.get("package_conf")
        self.config = read_user_config(config_path + '/sampleProp.conf')

        # Register device
        ram_device = SimulatedDevice(self.config['DeviceName'], "Device-RAM")
        self.reg_ram_device = self.iotcc.register(ram_device)
        self.iotcc.set_properties(self.reg_ram_device, self.config['DevicePropList'])

        self.iotcc.create_relationship(self.iotcc_edge_system, self.reg_ram_device)

        # Create metrics
        self.metrics = []

        mem_free_metric = Metric(
            name="Memory Free",
            unit=None,
            interval=10,
            sampling_function=read_mem_free
        )
        reg_mem_free_metric = self.iotcc.register(mem_free_metric)
        self.iotcc.create_relationship(self.reg_ram_device, reg_mem_free_metric)
        reg_mem_free_metric.start_collecting()
        self.metrics.append(reg_mem_free_metric)

        # Use the iotcc_device_name as identifier in the registry to easily refer the device in other packages
        registry.register("reg_ram_device", self.reg_ram_device)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()

        #Unregister iotcc device
        if self.config['ShouldUnregisterOnUnload'] == "True":
            self.iotcc.unregister(self.reg_ram_device)
