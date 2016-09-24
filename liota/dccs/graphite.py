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
from liota.entities.entity import Entity
from liota.dccs.dcc import DataCenterComponent
from liota.entities.metrics.registered_metric import RegisteredMetric


log = logging.getLogger(__name__)


class Graphite(DataCenterComponent):

    def __init__(self, comms):
        DataCenterComponent.__init__(self, comms=comms)

    def register(self, entity_obj):
        if not isinstance(entity_obj, Entity):
            raise TypeError
        DataCenterComponent.register(self, entity_obj)
        return entity_obj.register(self, None)

    def _create_relationship(self, entity_parent, entity_child):
        pass

    def _format_data(self, reg_metric):
        met_cnt = reg_metric.values.qsize()
        message = ''
        if met_cnt == 0:
            return
        for _ in range(met_cnt):
            v = reg_metric.values.get(block=True)
            if v is not None:
                # Graphite expects time in seconds, not milliseconds. Hence,
                # dividing by 1000
                message += '%s %s %d\n' % (reg_metric.ref_entity.name,
                                           v[1], v[0] / 1000)
        if message == '':
            return
        log.debug("Formatted message: {0}".format(message))
        return message

    def publish(self, reg_metric):
        if not isinstance(reg_metric, RegisteredMetric):
            raise TypeError
        message = self._format_data(reg_metric)
        self.comms.send(message)

    def set_properties(self, reg_entity, properties):
        raise NotImplementedError
