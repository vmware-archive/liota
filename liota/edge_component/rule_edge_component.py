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

import logging
import types

from liota.edge_component.edge_component import EdgeComponent
from liota.entities.registered_entity import RegisteredEntity
from liota.entities.edge_systems.edge_system import EdgeSystem
from liota.entities.devices.device import Device
from liota.entities.metrics.metric import Metric
from liota.entities.metrics.registered_metric import RegisteredMetric

log = logging.getLogger(__name__)

class RuleEdgeComponent(EdgeComponent):
	def __init__(self, model_rule, exceed_limit_consecutive, actuator_udm):
		if model_rule is None:
			raise TypeError("Model rule must be specified.")

		if not isinstance(model_rule, types.LambdaType):
			raise TypeError("Model rule must be a lambda function.")

		if model_rule.__name__ != "<lambda>":
			raise TypeError("Model rule must be a lambda function.")			

		if type(exceed_limit_consecutive) is not int:
			raise ValueError("exceed_limit should be a integer value.")

		self.model_rule = model_rule
		self.actuator_udm = actuator_udm
		self.exceed_limit = exceed_limit_consecutive
		self.counter = 0

	def register(self, entity_obj):
		if isinstance(entity_obj, Metric):
			return RegisteredMetric(entity_obj, self, None)
		else:
			return RegisteredEntity(entity_obj, self, None)

	def create_relationship(self, reg_entity_parent, reg_entity_child):
		reg_entity_child.parent = reg_entity_parent	

	def process(self, message):
		if not isinstance(self.actuator_udm, types.FunctionType):
			raise TypeError("actuator_udm must be of function type.")
		result = self.model_rule(message)
		self.counter = 0 if(result==0) else self.counter+1
		if(self.counter>=self.exceed_limit):
			self.counter=0
			self.actuator_udm(1)
		else:
			self.actuator_udm(0)

	def _format_data(self, reg_metric):
		met_cnt = reg_metric.values.qsize()
		if met_cnt == 0:
			return
		for _ in range(met_cnt):	
			metric_value = reg_metric.values.get(block=True)
			if metric_value is not None:
				# metric_value[1] as metric_value is a list having both timestamp and value
				return metric_value[1]

	def build_model(self):
		pass	

	def load_model(self):
		pass

	def unregister(self):
		pass
