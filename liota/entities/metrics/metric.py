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

import pint
from liota.entities.entity import Entity
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.lib.utilities.utility import systemUUID


class Metric(Entity):
    """
    Metric represents sensor values collected from Device (Sensors/Things) or EdgeSystem (Gateway).
    """

    def __init__(self, name, entity_type="Metric",
                 unit=None,
                 interval=60,
                 aggregation_size=1,
                 sampling_function=None
                 ):
        """
        Init method for Metric

        :param name: Metric name
        :param entity_type: Entity type which is "Metric"
        :param unit: Unit of representation
        :param interval: Sampling interval (in seconds ) at which the metric should be collected
        :param aggregation_size: Number of times the metric should be collected before publishing it to the DCC
        :param sampling_function: User defined function from which the metric should be collected
        """
        if not (unit is None or isinstance(unit, pint.unit._Unit)) \
                or not (
            isinstance(interval, int) or isinstance(interval, float)
        ) \
                or not isinstance(aggregation_size, int):
            raise TypeError()
        super(Metric, self).__init__(
            name=name,
            entity_id=systemUUID().get_uuid(name),
            entity_type=entity_type
        )
        self.unit = unit
        self.interval = interval
        self.aggregation_size = aggregation_size
        self.sampling_function = sampling_function

    def register(self, dcc_obj, reg_entity_id):
        """
        This method returns RegisteredMetric Object

        :param dcc_obj: DCC Object
        :param reg_entity_id: RegisteredEntity ID
        :return:
        """
        return RegisteredMetric(self, dcc_obj, reg_entity_id)
