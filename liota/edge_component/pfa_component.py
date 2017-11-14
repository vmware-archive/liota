
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
import os
from liota.edge_component.edge_component import EdgeComponent
import csv
from liota.entities.metrics.metric import Metric
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.entities.registered_entity import RegisteredEntity
import titus.prettypfa
import json
from titus.genpy import PFAEngine

log = logging.getLogger(__name__)


class PFAComponent(EdgeComponent):

    def __init__(self, model_path, actuator_udm):
        super(PFAComponent, self).__init__(model_path, actuator_udm)
        if not os.path.exists(model_path):
			raise IOError("File does not exist: {} ".format(model_path))
        self.model = None
        self.load_model()

    def load_model(self):
        log.info("Loading model..")
        self.model, = PFAEngine.fromJson(json.load(open(self.model_path)))

    def register(self, entity_obj):
        if isinstance(entity_obj, Metric):
            return RegisteredMetric(entity_obj, self, None)
        else:
            return RegisteredEntity(entity_obj, self, None)

    def create_relationship(self, reg_entity_parent, reg_entity_child):
        pass

    def process(self,message):
        self.actuator_udm(self.model.action(message))

    def _format_data(self, reg_metric):
        met_cnt = reg_metric.values.qsize()
        if met_cnt == 0:
            return
        for _ in range(met_cnt):
            metric_value = reg_metric.values.get(block=True)
            if metric_value is not None:
                # metric_value[1] as metric_value is a list having both timestamp and value
                return metric_value[1]

    def set_properties(self, reg_entity, properties):
        pass

    def unregister(self, entity_obj):
        pass

    def build_model(self):
        pass
