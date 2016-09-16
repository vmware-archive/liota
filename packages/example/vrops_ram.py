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

def read_mem_free():
    from linux_metrics import mem_stat

    return round((mem_stat.mem_stats()[3]) / (1048576), 3)

class PackageClass(LiotaPackage):

    def run(self, registry):
        from liota.things.ram import RAM

        # Acquire resources from registry
        vrops = registry.get("vrops")
        vrops_gateway = registry.get("vrops_gateway")
        gateway = vrops_gateway.resource

        # Get values from configuration file
        config = {}
        config_path = registry.get("package_conf")
        execfile(config_path + "/sampleProp.conf", config)

        # Register device
        ram = RAM(config['Device1Name'], 'Read', gateway)
        vrops_ram = vrops.register(ram)
        assert(vrops_ram.registered)
        vrops.set_properties(vrops_ram, config['Device1PropList'])

        # Create metrics
        self.metrics = []
        mem_free = vrops.create_metric(
                vrops_ram, "Memory_Free",
                unit=None,
                sampling_interval_sec=10,
                sampling_function=read_mem_free
            )
        mem_free.start_collecting()
        self.metrics.append(mem_free)

        registry.register("vrops_ram", vrops_ram)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()
