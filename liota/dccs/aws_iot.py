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

from liota.dccs.dcc import DataCenterComponent
from liota.entities.edge_systems.edge_system import EdgeSystem
from liota.entities.devices.device import Device
from liota.entities.metrics.metric import Metric
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.entities.registered_entity import RegisteredEntity
from liota.lib.utilities.si_unit import parse_unit
from collections import OrderedDict
import json
import logging

log = logging.getLogger(__name__)


class AWSIoT(DataCenterComponent):
    """
    DCC for AWS IoT platform. AWSMQTTDccComms is used as transport
    """
    def __init__(self, con, qos=1, enclose_metadata=False):
        """
        :param con: AWSMQTTDccComms Object
        :param qos: 0 or 1
        :param enclose_metadata: Include Gateway, Device and Metric names as part of payload or not
        """
        super(AWSIoT, self).__init__(con)
        if qos in range(0, 2):
            self.qos = qos
        else:
            raise ValueError("QoS must either be 0 or 1")
        self.enclose_metadata = enclose_metadata

    def register_entity(self, parent_entity, child_entity):
        """
        Returns RegisteredEntity and also creates Parent-Child Relationship

        :param parent_entity: EdgeSystem or a RegisteredEntity Object
        :param child_entity: Device or a Metric Object or None
        :return: RegisteredEntity or RegisteredMetric
        """
        if isinstance(parent_entity, EdgeSystem) and child_entity is None:
            return RegisteredEntity(parent_entity, self, None)

        elif isinstance(parent_entity, RegisteredEntity) and isinstance(child_entity, Device):
            reg_entity = RegisteredEntity(child_entity, self, None)
            self.create_relationship(parent_entity, reg_entity)
            return reg_entity

        elif isinstance(parent_entity, RegisteredEntity) and isinstance(child_entity, Metric):
            reg_metric = RegisteredMetric(child_entity, self, None)
            self.create_relationship(parent_entity, reg_metric)
            return reg_metric

        else:
            log.error("Illegal Registration attempted between Parent Entity:{0} and Child Entity:{1}".
                      format(parent_entity, child_entity))
            raise TypeError("Illegal Registration attempted.")

    def create_relationship(self, reg_entity_parent, reg_entity_child):
        """
        This method creates Parent-Child relationship.  Supported relationships are:

               EdgeSystem
                   |                                      EdgeSystem
                Device                   (or)                |
                   |                                    RegisteredMetric
             RegisteredMetric

        However, A single EdgeSystem can have multiple child Devices and a each Device can have
        multiple child Metrics.

        :param reg_entity_parent: Registered EdgeSystem or Device Object
        :param reg_entity_child:  Registered Device or Metric Object
        :return: None
        """
        if not isinstance(reg_entity_parent.ref_entity, EdgeSystem) and \
                not isinstance(reg_entity_parent.ref_entity, Device):
            raise TypeError("reg_entity_parent should either be a Registered EdgeSystem or a Device")

        if not isinstance(reg_entity_child.ref_entity, Device) and \
                not isinstance(reg_entity_child, RegisteredMetric):
            raise TypeError("reg_entity_child should either be a Registered Device or Metric")

        reg_entity_child.parent = reg_entity_parent

    def _get_publish_topic(self, reg_metric):
        """
        :param reg_metric: RegisteredMetric Object
        :return: MQTT publish topic based on Parent Child relationship
        """
        if not isinstance(reg_metric, RegisteredMetric):
            raise TypeError("RegisteredMetric is expected")

        def extract_topic(reg_entity):
            """
            Recursive function for extracting topic
            :param reg_entity: RegisteredEntity Object
            :return:
            """
            if reg_entity is None:
                return ""
            else:
                return extract_topic(reg_entity.parent) + reg_entity.ref_entity.name + '/'
        return extract_topic(reg_metric.parent) + reg_metric.ref_entity.name

    def _format_data(self, reg_metric):
        """
        :param reg_metric: Registered Metric Object
        :return: Payload in JSON format
        """
        _list = []
        met_cnt = reg_metric.values.qsize()
        if met_cnt > 0:
            for _ in range(met_cnt):
                m = reg_metric.values.get(block=True)
                if m is not None:
                    _list.append(OrderedDict([('value', m[1]), ('timestamp', m[0])]))
        payload = OrderedDict()
        if self.enclose_metadata:
            _meta_data = self._get_publish_topic(reg_metric).split("/")
            if len(_meta_data) == 3:
                payload['gateway_name'] = _meta_data[0]
                payload['device_name'] = _meta_data[1]
                payload['metric_name'] = _meta_data[2]
            else:
                payload['gateway_name'] = _meta_data[0]
                payload['metric_name'] = _meta_data[1]
        payload['metric_data'] = [_ for _ in _list]
        payload['unit'] = parse_unit(reg_metric.ref_entity.unit)[1]
        return json.dumps(payload)

    def publish(self, reg_metric):
        """
        Publishes message to AWS IoT in JSON format.
        :param reg_metric: Registered Metric Object
        :return: None
        """
        log.debug("Publishing to AWS IoT")
        self.comms.publish(self._get_publish_topic(reg_metric), self._format_data(reg_metric), self.qos)

    def set_properties(self, reg_entity, properties):
        raise NotImplementedError

    def register(self, entity_obj):
        raise NotImplementedError
