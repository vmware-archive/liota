# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2015-2016 VMware, Inc. All Rights Reserved.             	      #
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

from liota.dcc_comms.socket_comms import SocketDccComms
from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
from liota.lib.utilities.utility import read_user_config
from liota.device_comms.cip_ethernet_ip_device_comms import CipEtherNetIpDeviceComms 
from liota.entities.devices.simulated_device import SimulatedDevice



config = read_user_config('sampleProp.conf')

def read_value(conn, tag, index):
    value = conn.receive(tag, index)
    return value


if __name__ == "__main__":

    cip_ethernet_ip_conn =  CipEtherNetIpDeviceComms(host=config['CipEtherNetIp'])
    
    tag = config['Tag']
    index = config['Index']
    
    graphite = Graphite(SocketDccComms(ip=config['GraphiteIP'],
                               port=config['GraphitePort']))
	

    cip_ethernet_device = SimulatedDevice(config['DeviceName'], "Test")
    reg_cip_ethernet_device = graphite.register(cip_ethernet_device)


    cip_ethernet_device_metric_name = "model.cipEthernetIP"


	cip_ethernet_device_metric = Metric(
		name=cip_ethernet_device_metric_name,
		unit=None,
		interval=5,
		sampling_function=lambda:read_value(cip_ethernet_ip_conn, tag, index)
	)

	reg_cip_ethernet_device_metric = graphite.register(cip_ethernet_device_metric)
	graphite.create_relationship(reg_cip_ethernet_device, reg_cip_ethernet_device_metric)
	reg_cip_ethernet_device_metric.start_collecting()
