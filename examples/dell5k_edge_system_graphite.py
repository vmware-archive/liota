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

from linux_metrics import cpu_stat
from liota.dcc_comms.socket_comms import SocketDccComms
from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
from liota.lib.utilities.utility import read_user_config

# getting values from conf file
config = read_user_config('sampleProp.conf')

def read_cpu_utilization(sample_duration_sec=1):
    cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
    return round((100 - cpu_pcts['idle']), 2)

# ---------------------------------------------------------------------------
# In this example, we demonstrate how a Dell5000 Gateway metric (e.g.,
# CPU utilization) can be directed to graphite data center component
# using Liota. The program illustrates the ease of use Liota brings
# to IoT application developers.

if __name__ == '__main__':

    edge_system = Dell5KEdgeSystem(config['EdgeSystemName'])

    # Sending data to Graphite data center component
    # Socket is the underlying transport used to connect to the Graphite
    # instance
    graphite = Graphite(SocketDccComms(ip=config['GraphiteIP'],
                               port=config['GraphitePort']))
    graphite_reg_edge_system = graphite.register(edge_system)

    metric_name = config['MetricName']
    cpu_utilization = Metric(
        name=metric_name,
        unit=None,
        interval=10,
        aggregation_size=2,
        sampling_function=read_cpu_utilization
    )
    reg_cpu_utilization = graphite.register(cpu_utilization)
    graphite.create_relationship(graphite_reg_edge_system, reg_cpu_utilization)
    reg_cpu_utilization.start_collecting()
