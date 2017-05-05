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

import random
import time

from liota.dcc_comms.socket_comms import SocketDccComms
from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.simulated_edge_system import SimulatedEdgeSystem
from liota.lib.utilities.utility import getUTCmillis, read_user_config

# getting values from conf file
config = read_user_config('sampleProp.conf')

# Simple sampling function for metric returning the current sample value
def simulated_value_sampling_function():
    return random.randint(0, 20)

# Sampling function demonstrating metrics where the sample time can be different then the current time
def simulated_timestamp_value_sampling_function():
    current_time = getUTCmillis()
    # Random time in the last 5 seconds, when the sample was generated.
    sample_generation_time = current_time - random.randint(0, 5)
    sample_value = random.randint(0, 20)
    return (sample_generation_time, sample_value)

# Sampling function demonstrating metrics which provide a list of sample values from the last time it was called.
def simulated_list_of_timestamps_values_sampling_function():
    random.seed(time.clock())
    current_time = getUTCmillis()
    list_of_timestamp_value_tuples = []
    for step in range(0, 25, 5):
        list_of_timestamp_value_tuples.append((current_time - step*1000, random.randint(0, 20)))
    return list_of_timestamp_value_tuples

# ---------------------------------------------------------------------------
# In this example, we demonstrate how data for a simulated metric generating
# random numbers can be directed to graphite data center component using Liota.
# The program illustrates the ease of use Liota brings to IoT application
# developers.

if __name__ == '__main__':

    edge_system = SimulatedEdgeSystem(config['EdgeSystemName'])

    # Sending data to Graphite data center component
    # Socket is the underlying transport used to connect to the Graphite
    # instance
    graphite = Graphite(SocketDccComms(ip=config['GraphiteIP'],
                               port=config['GraphitePort']))
    graphite_reg_edge_system = graphite.register(edge_system)

    # A simple simulated metric which generates metric value every 10 seconds
    simple_metric_name = config['MetricName']
    simple_metric = Metric(name=simple_metric_name, interval=10,
                              sampling_function=simulated_value_sampling_function)
    reg_simple_metric = graphite.register(simple_metric)
    graphite.create_relationship(graphite_reg_edge_system, reg_simple_metric)
    reg_simple_metric.start_collecting()

    # A simulated metric producing sample value along with timestamp when the sample was generated
    metric_with_own_ts_name = config['MetricWithOwnTsName']
    metric_with_own_ts = Metric(name=metric_with_own_ts_name, interval=10,
                              sampling_function=simulated_timestamp_value_sampling_function)
    reg_metric_with_own_ts = graphite.register(metric_with_own_ts)
    graphite.create_relationship(graphite_reg_edge_system, reg_metric_with_own_ts)
    reg_metric_with_own_ts.start_collecting()

    # A simulated metric producing a list of sample values along with their timestamps in the last polling interval
    bulk_collected_metric_name = config['BulkCollectedMetricName']
    bulk_collected_metric = Metric(name=bulk_collected_metric_name, interval=30,
                              aggregation_size=10, sampling_function=simulated_list_of_timestamps_values_sampling_function)
    reg_bulk_collected_metric = graphite.register(bulk_collected_metric)
    graphite.create_relationship(graphite_reg_edge_system, reg_bulk_collected_metric)
    reg_bulk_collected_metric.start_collecting()
