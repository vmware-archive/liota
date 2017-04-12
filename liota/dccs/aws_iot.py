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

import json
import logging
from collections import OrderedDict

from liota.dccs.dcc import DataCenterComponent
from liota.entities.registered_entity import RegisteredEntity
from liota.entities.edge_systems.edge_system import EdgeSystem
from liota.entities.devices.device import Device
from liota.entities.metrics.metric import Metric
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.lib.utilities.si_unit import parse_unit, UnsupportedUnitError

log = logging.getLogger(__name__)


class AWSIoT(DataCenterComponent):
    """
    DCC for AWSIoT Platform.
    """
    def __init__(self, con, enclose_metadata=False):
        """
        :param con: DccComms Object
        :param enclose_metadata: Include Gateway, Device and Metric names as part of payload or not
        """
        super(AWSIoT, self).__init__(
            comms=con
        )
        self.enclose_metadata = enclose_metadata

    def register(self, entity_obj):
        """
        :param entity_obj: Entity Object
        :return: RegisteredEntity Object
        """
        log.info("Registering resource with AWSIoT DCC {0}".format(entity_obj.name))
        super(AWSIoT, self).register(entity_obj)
        if isinstance(entity_obj, Metric):
            return RegisteredMetric(entity_obj, self, None)
        else:
            return RegisteredEntity(entity_obj, self, None)

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

        :param reg_entity_parent: Registered EdgeSystem or Registered Device Object
        :param reg_entity_child:  Registered Device or Registered Metric Object
        :return: None
        """
        # Validating here helps in enclose_metadata
        if not isinstance(reg_entity_parent.ref_entity, EdgeSystem) and \
                not isinstance(reg_entity_parent.ref_entity, Device):
            log.error("reg_entity_parent should either be a Registered EdgeSystem or a Device")
            raise TypeError("reg_entity_parent should either be a Registered EdgeSystem or a Device")

        if not isinstance(reg_entity_child.ref_entity, Device) and \
                not isinstance(reg_entity_child, RegisteredMetric):
            log.error("reg_entity_child should either be a Registered Device or Metric")
            raise TypeError("reg_entity_child should either be a Registered Device or Metric")

        reg_entity_child.parent = reg_entity_parent

    def _get_entity_hierarchy(self, reg_entity):
        """
        NOTE: This method should be moved to utility if other DCCs require this functionality.
        :param reg_entity: RegisteredMetric Object
        :return: A list with entity names
                 - [edge_system_name, device_name, metric_name] (or)
                 - [edge_system_name, metric_name]
        """
        if not isinstance(reg_entity, RegisteredEntity):
            log.error("RegisteredEntity is expected")
            raise TypeError("RegisteredEntity is expected")

        def extract_hierarchy(reg_entity):
            """
            Recursive function to get entity names
            :param reg_entity: RegisteredEntity Object
            :return:
            """
            if reg_entity is None:
                return []
            return extract_hierarchy(reg_entity.parent) + [reg_entity.ref_entity.name]

        return extract_hierarchy(reg_entity)

    def _format_data(self, reg_metric):
        """
        :param reg_metric: Registered Metric Object
        :return: Payload in JSON format
        """
        met_cnt = reg_metric.values.qsize()
        if 0 == met_cnt:
            return

        _list = []
        for _ in range(met_cnt):
            m = reg_metric.values.get(block=True)
            if m is not None:
                _list.append(OrderedDict([('value', m[1]), ('timestamp', m[0])]))

        payload = OrderedDict()
        if self.enclose_metadata:
            _entity_hierarchy = self._get_entity_hierarchy(reg_metric)
            #  EdgeSystem and Device's name will be added with payload
            if len(_entity_hierarchy) == 3:
                payload['edge_system_name'] = _entity_hierarchy[0]
                payload['device_name'] = _entity_hierarchy[1]
            # EdgeSystem's name will be added with payload
            elif len(_entity_hierarchy) == 2:
                payload['edge_system_name'] = _entity_hierarchy[0]
            else:
                # Not raising error.
                # Metrics can be published even if error occurred while
                # constructing payload for enclose_metadata
                log.error("Error occurred while constructing payload")
        payload['metric_name'] = reg_metric.ref_entity.name
        payload['metric_data'] = [_ for _ in _list]
        # TODO: Make this as part of si_unit.py
        # Handling Base, Derived and Prefixed Units
        if reg_metric.ref_entity.unit is None:
            payload['unit'] = 'null'
        else:
            try:
                unit_tuple = parse_unit(reg_metric.ref_entity.unit)
                if unit_tuple[0] is None:
                    # Base and Derived Units
                    payload['unit'] = unit_tuple[1]
                else:
                    # Prefixed or non-SI Units
                    payload['unit'] = unit_tuple[0] + unit_tuple[1]
            except UnsupportedUnitError as err:
                # Not raising error.
                # Metrics can be published even if unit is unsupported
                payload['unit'] = 'null'
                log.error(str(err))
        return json.dumps(payload)

    def set_properties(self, reg_entity, properties):
        raise NotImplementedError

    def unregister(self, entity_obj):
        raise NotImplementedError
