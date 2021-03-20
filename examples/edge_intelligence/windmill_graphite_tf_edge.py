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

# This example depicts how edge component can be used to take actions locally based on trained TensorFlow model
# and actions can then be send to device using actuator_udm method defined here, which is currently just printing
# the returned value is from TensorFlowEdgeComponent as actions. Only the gateway metrics are being published to Graphite DCC.

import math
import random

from linux_metrics import cpu_stat, mem_stat
from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
from liota.dcc_comms.socket_comms import SocketDccComms
from liota.dccs.dcc import RegistrationFailure
from liota.edge_component.tensorflow_edge_component import TensorFlowEdgeComponent 
from liota.lib.utilities.utility import read_user_config

# getting values from conf file
config = {}
execfile('../sampleProp.conf', config)

def read_cpu_procs():
	return cpu_stat.procs_running()

def read_cpu_utilization(sample_duration_sec=1):
	cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
	return round((100 - cpu_pcts['idle']), 2)

def read_mem_free():
	total_mem = round(mem_stat.mem_stats()[1], 4)
	free_mem = round(mem_stat.mem_stats()[3], 4)
	mem_free_percent = ((total_mem - free_mem) / total_mem) * 100
	return round(mem_free_percent, 2)

# actuator_udm can be used to pass on the value to the actuator, as of now we are printing them
def actuator_udm(value):
	print value

# simulating windmill RPM which is a device connected to Edge.
def get_rpm():
	return random.randint(10,25)

# ---------------------------------------------------------------------------------------
# In this example, we demonstrate how metrics collected from a SensorTag device over BLE
# can be directed to graphite data center component using Liota.
# The program illustrates the ease of use Liota brings to IoT application developers.

if __name__ == '__main__':

	# create a data center object, graphite in this case, using websocket as a transport layer
	graphite = Graphite(SocketDccComms(ip=config['GraphiteIP'],
									   port=config['GraphitePort']))

	try:
		# create a System object encapsulating the particulars of a IoT System
		# argument is the name of this IoT System
		edge_system = Dell5KEdgeSystem(config['EdgeSystemName'])

		# resister the IoT System with the graphite instance
		# this call creates a representation (a Resource) in graphite for this IoT System with the name given
		reg_edge_system = graphite.register(edge_system)

		# Operational metrics of EdgeSystem
		cpu_utilization_metric = Metric(
			name="windmill.CPU_Utilization",
			unit=None,
			interval=10,
			aggregation_size=2,
			sampling_function=read_cpu_utilization
		)
		reg_cpu_utilization_metric = graphite.register(cpu_utilization_metric)
		graphite.create_relationship(reg_edge_system, reg_cpu_utilization_metric)
		# call to start collecting values from the device or system and sending to the data center component
		reg_cpu_utilization_metric.start_collecting()

		cpu_procs_metric = Metric(
			name="windmill.CPU_Process",
			unit=None,
			interval=6,
			aggregation_size=8,
			sampling_function=read_cpu_procs
		)
		reg_cpu_procs_metric = graphite.register(cpu_procs_metric)
		graphite.create_relationship(reg_edge_system, reg_cpu_procs_metric)
		reg_cpu_procs_metric.start_collecting()

		mem_free_metric = Metric(
			name="windmill.Memory_Free",
			unit=None,
			interval=10,
			sampling_function=read_mem_free
		)
		reg_mem_free_metric = graphite.register(mem_free_metric)
		graphite.create_relationship(reg_edge_system, reg_mem_free_metric)
		reg_mem_free_metric.start_collecting()

		tf_rpm_metric = Metric(
			name="windmill.RPM",
			unit=None,
			interval=1,
			aggregation_size=1,
			sampling_function=get_rpm
		)

		# ModelPath can be edited in the sampleProp.conf file
		# pass value to actuator as of now the actuator_udm prints the value on the console
		# TensorFlow edge component is a part of edge intelligence and analytics for Liota, uses tensorflow trained model
		# for analytics.
		edge_component = TensorFlowEdgeComponent(config['ModelPath'], actuator_udm=actuator_udm)
		tf_reg_rpm_metric = edge_component.register(tf_rpm_metric)
		tf_reg_rpm_metric.start_collecting()

	except RegistrationFailure:
		print "Registration to graphite failed"
