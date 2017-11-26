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
from liota.dcc_comms.socket_comms import SocketDccComms
from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
from liota.lib.utilities.utility import read_user_config
from liota.device_comms.cip_ethernet_ip_device_comms import CipEtherNetIpDeviceComms
from liota.entities.devices.simulated_device import SimulatedDevice


dependencies = ["graphite"]


#  Reading values from the cip ethernetip server.
def read_value(conn, tag, index):
    value = conn.receive(tag, index)
    return value


# ---------------------------------------------------------------------------------------------------------------
# In this example, we demonstrate how data is read from the cip ethernet server every 7 seconds.
# The value got from the user-defined method is directed to Graphite data center component using Liota.
#----------------------------------------------------------------------------------------------------------------



class PackageClass(LiotaPackage):

    def run(self, registry):

        # Acquire resources from registry
        graphite = registry.get("graphite")

        # Get values from configuration file
        config_path = registry.get("package_conf")
        self.config = read_user_config(config_path + '/sampleProp.conf')

        self.cip_ethernet_ip_conn =  CipEtherNetIpDeviceComms(host=self.config['CipEtherNetIp'])
    
	self.tag = self.config['Tag']         
        self.index = self.config['Index']
                               
        #  Creating Simulated Device
        cip_ethernet_device = SimulatedDevice(self.config['DeviceName'], "Test")
        #  Registering Device and creating Parent-Child relationship
	reg_cip_ethernet_device = graphite.register(cip_ethernet_device)

        # Create metrics
        self.metrics = []

        cip_ethernet_device_metric_name = "CIP.ethernetIP"

        #  Creating CIP device Metric
        cip_ethernet_device_metric = Metric(
            name=cip_ethernet_device_metric_name,
            unit=None,
            interval=7,
            sampling_function=lambda: read_value(self.cip_ethernet_ip_conn, self.tag, self.index)
        )

        #  Registering Metric and creating Parent-Child relationship
        reg_cip_ethernet_device_metric = graphite.register(cip_ethernet_device_metric)
        graphite.create_relationship(
            reg_cip_ethernet_device,
            reg_cip_ethernet_device_metric)
        reg_cip_ethernet_device_metric.start_collecting()
        self.metrics.append(reg_cip_ethernet_device_metric)

    def clean_up(self):
	for metric in self.metrics:
            metric.stop_collecting()
	self.cip_ethernet_ip_conn._disconnect()
