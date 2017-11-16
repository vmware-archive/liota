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
from liota.device_comms.EtherNetIP_DeviceComms import CipEtherNetIpDeviceComms
from liota.entities.devices.simulated_device import SimulatedDevice


dependencies = ["graphite"]


def read_value(conn):
    value = conn.read()
    return value


class PackageClass(LiotaPackage):

    def run(self, registry):

        # Acquire resources from registry
        graphite = registry.get("graphite")

        config_path = registry.get("package_conf")

        self.config = read_user_config(config_path + '/sampleProp.conf')

        self.ethernetIP_conn =  CipEtherNetIpDeviceComms(host=self.config['EtherNetIP'], port, timeout, dialect,
                                                profiler, udp=False, broadcast=False, source_address)

        ethernet_device = SimulatedDevice(self.config['DeviceName'], "Test")
        reg_ethernet_device = graphite.register(ethernet_device)

        self.metrics = []

        ethernet_device_metric_name = "CIP.ethernetIP"

        ethernet_device_metric = Metric(
            name=ethernet_device_metric_name,
            unit=None,
            interval=5,
            sampling_function=lambda: read_value(self.ethernetIP_conn)
        )

        reg_ethernet_device_metric = graphite.register(ethernet_device_metric)
        graphite.create_relationship(
            reg_ethernet_device,
            reg_ethernet_device_metric)
        reg_ethernet_device_metric.start_collecting()
        self.metrics.append(reg_ethernet_device_metric)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()
	self.ethernetIP_conn._disconnect()
