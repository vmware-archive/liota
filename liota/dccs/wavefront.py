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
from liota.dccs.dcc import DataCenterComponent
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.entities.metrics.metric import Metric
from liota.entities.registered_entity import RegisteredEntity

log = logging.getLogger(__name__)

class Wavefront(DataCenterComponent):
	def __init__(self, comms):
		super(Wavefront, self).__init__(
			comms=comms
		)
		self.comms = comms

	def register(self, entity_obj):
		log.info("Registering resource with Wavefront DCC {0}".format(entity_obj.name))
		if isinstance(entity_obj, Metric):
			return RegisteredMetric(entity_obj, self, None)
		else:
			return RegisteredEntity(entity_obj, self, None)

	def create_relationship(self, reg_entity_parent, reg_entity_child):
		reg_entity_child.parent = reg_entity_parent

	def _format_data(self, reg_metric):
		met_cnt = reg_metric.values.qsize()
		message = ''
		host = ''
		device_name = ''
		metric_name = ''
		if met_cnt == 0:
			return
		for _ in range(met_cnt):
			v = reg_metric.values.get(block=True)
			if v is not None:
				device_name = (reg_metric.parent).ref_entity.name
				metric_name = reg_metric.ref_entity.name
				if (reg_metric.parent).parent:
					host = (reg_metric.parent).parent.ref_entity.entity_id+"."+(reg_metric.parent).ref_entity.entity_id
				else:
					host = (reg_metric.parent).ref_entity.entity_id #if device is not available, only gateway uuid
				
				metric_unit = str(reg_metric.ref_entity.unit)
				metric_unit = ''.join(metric_unit.split())
				message += '{0},unit={5},host={1} {2}={3} {4}'.format(device_name,host,metric_name,v[1],
														v[0]*1000000,metric_unit)
		if message == '':
			return
		log.info ("Publishing values to Wavefront DCC")
		log.debug("Device name: {0}".format(device_name))
		log.debug("Metric name: {0}".format(metric_name))
		log.debug("Host name: {0}".format(host))
		log.debug("Formatted message: {0}".format(message))
		return message

	def set_properties(self, reg_entity, properties):
		raise NotImplementedError

	def unregister(self, entity_obj):
		raise NotImplementedError
