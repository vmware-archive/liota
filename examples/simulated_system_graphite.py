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

import ConfigParser
import random

from liota.dcc_comms.socket_comms import Socket
from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.systems.simulated_system import SimulatedSystem


# getting values from conf file
config = ConfigParser.ConfigParser()
config.readfp(open('sampleProp.conf'))

# Random number generator, simulating random metric readings.


def simulated_sampling_function():
    return random.randint(0, 20)

# ---------------------------------------------------------------------------
# In this example, we demonstrate how data for a simulated metric generating
# random numbers can be directed to graphite data center component using Liota.
# The program illustrates the ease of use Liota brings to IoT application
# developers.

if __name__ == '__main__':

    system = SimulatedSystem(config.get('DEFAULT', 'GatewayName'))

    # Sending data to Graphite data center component
    # Socket is the underlying transport used to connect to the Graphite
    # instance
    graphite = Graphite(Socket(ip=config.get('GRAPHITE', 'IP'),
                               port=config.getint('GRAPHITE', 'Port')))
    graphite_reg_system = graphite.register(system)
    metric_name = config.get('DEFAULT', 'MetricName')
    simulated_metric = Metric(name=metric_name, parent=system, entity_id=metric_name,
                              interval=10, sampling_function=simulated_sampling_function)
    reg_metric = graphite.register_metric(simulated_metric)
    reg_metric.start_collecting()
