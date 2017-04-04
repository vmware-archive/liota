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

from liota.entities.registered_entity import RegisteredEntity
from liota.lib.utilities.si_unit import parse_unit, UnsupportedUnitError

log = logging.getLogger(__name__)


def get_entity_hierarchy(reg_entity):
    """
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


def get_formatted_data(reg_metric, enclose_metadata):
    """
    :param reg_metric: Registered Metric Object
    :param enclose_metadata: Include Gateway, Device and Metric names as part of payload or not
    :return: Payload in JSON format or None
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
    if enclose_metadata:
        _entity_hierarchy = get_entity_hierarchy(reg_metric)
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
