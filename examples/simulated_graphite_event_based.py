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

import Queue
import random
import time
import thread
from liota.dcc_comms.socket_comms import SocketDccComms
from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.dk300_edge_system import Dk300EdgeSystem
from liota.lib.utilities.utility import read_user_config

# getting values from conf file
config = read_user_config('sampleProp.conf')

comms_channel = Queue.Queue() # channel between device and a udm used for a metric

#simulates a device putting data into a comms channel at random intervals
def simulated_event_device(write_channel):
    while(True):
        time.sleep(random.randint(1,10))
        write_channel.put(random.randint(1,300))

# starting the simulated device
thread.start_new_thread(simulated_event_device, (comms_channel,))

def udm1():
    return comms_channel.get(block=True)

#---------------------------------------------------------------------------
# In this example, we demonstrate how an event stream of data can be directed to graphite
# data center component using Liota by setting sampling_interval_sec parameter to zero.

if __name__ == '__main__':

    edge_system = Dk300EdgeSystem(config['EdgeSystemName'])

    # Sending data to Graphite data center component
    # Socket is the underlying transport used to connect to the Graphite
    # instance
    graphite = Graphite(SocketDccComms(ip=config['GraphiteIP'],
                               port=config['GraphitePort']))
    graphite_reg_edge_system = graphite.register(edge_system)

    metric_name = config['MetricName']
    content_metric = Metric(
        name=metric_name,
        unit=None,
        interval=0,
        aggregation_size=6,
        sampling_function=udm1
    )
    reg_content_metric = graphite.register(content_metric)
    graphite.create_relationship(graphite_reg_edge_system, reg_content_metric)
    reg_content_metric.start_collecting()
