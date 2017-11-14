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

from liota.core.package_manager import LiotaPackage

dependencies = ["graphite", "examples/windmill_simulator"]

vib_queue = Queue.Queue()
action_taken = Queue.Queue()

class PackageClass(LiotaPackage):
	def create_udm(self, windmill_model):
		
		def get_windmill_vib():
			vib = windmill_model.get_vib()
			vib_queue.put(vib)
			return vib

		def get_vib_windmill_edge():
			return vib_queue.get(block=True)

		# you can write your own logic in this function in order to send value
		# to device if needed, currently action is being published to Graphite DCC
		def get_action(value):
			action_taken.put(value)

		def get_action_taken():
			return action_taken.get(block=True)

		self.get_windmill_vib = get_windmill_vib
		self.get_vib_windmill_edge = get_vib_windmill_edge
		self.get_action = get_action
		self.get_action_taken = get_action_taken

	def run(self, registry):
		from liota.entities.metrics.metric import Metric
		from liota.edge_component.rule_edge_component import RuleEdgeComponent

		windmill_simulator = registry.get("windmill_simulator")
		graphite = registry.get("graphite")
		graphite_windmill = graphite.register(windmill_simulator)

		self.create_udm(windmill_model=windmill_simulator)
		
		vib_limit = 0.59
		ModelRule = lambda value_collected : 1 if (value_collected>=vib_limit) else 0
		exceed_limit = 1
		rule_edge_component = RuleEdgeComponent(ModelRule, exceed_limit, self.get_action)
		
		self.metrics = []

		metric_name = "edge.vib"
		
		vib = Metric(
			name = metric_name,
			unit = None,
			interval=1,
			aggregation_size=1,
			sampling_function=self.get_windmill_vib
		)

		reg_windmill_vib = graphite.register(vib)
		graphite.create_relationship(graphite_windmill, reg_windmill_vib)
		reg_windmill_vib.start_collecting()
		self.metrics.append(reg_windmill_vib)
		
		rule_vib = Metric(
			name = metric_name,
			unit = None,
			interval=1,
			aggregation_size=1,
			sampling_function=self.get_vib_windmill_edge
		)

		reg_vib = rule_edge_component.register(rule_vib)
		reg_vib.start_collecting()
		self.metrics.append(reg_vib)

		action_taken = Metric(
			name = "edge.action",
			unit = None,
			interval=1,
			aggregation_size=1,
			sampling_function=self.get_action_taken
		)
		
		reg_windmill_action = graphite.register(action_taken)
		graphite.create_relationship(graphite_windmill, reg_windmill_action)
		reg_windmill_action.start_collecting()
		self.metrics.append(reg_windmill_action)

        def clean_up(self):
        	for metric in self.metrics:
        		metric.stop_collecting()
