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
from liota.entities.registered_entity import RegisteredEntity
from liota.entities.edge_systems.edge_system import EdgeSystem
from liota.entities.devices.device import Device
from liota.entities.metrics.metric import Metric
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.lib.utilities.dcc_utility import get_formatted_data

log = logging.getLogger(__name__)


class RabbitMQ(DataCenterComponent):
    """
    DCC for RabbitMQ.
    """
    def __init__(self, con, enclose_metadata=False):
        """
        :param con: DccComms Object
        :param enclose_metadata: Include Gateway, Device and Metric names as part of payload or not
        """
        super(RabbitMQ, self).__init__(
            comms=con
        )
        self.enclose_metadata = enclose_metadata

    def register(self, entity_obj):
        """
        :param entity_obj: Entity Object
        :return: RegisteredEntity Object
        """
        log.info("Registering resource with RabbitMQ DCC {0}".format(entity_obj.name))
        super(RabbitMQ, self).register(entity_obj)
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

    def _format_data(self, reg_metric):
        """
        :param reg_metric: Registered Metric Object
        :return: Payload in JSON format
        """
        return get_formatted_data(reg_metric, self.enclose_metadata)

    def consume(self, consume_msg_attr_list, auto_gen_callback=None):
        """
        Consume messages from AMQP broker
        :param consume_msg_attr_list: list of AmqpConsumeMessagingAttributes objects or None
        :param auto_gen_callback: callback method to be invoked for auto-generated AmqpConsumeMessagingAttributes
        :return:
        """
        self.comms.receive(consume_msg_attr_list, auto_gen_callback)

    def stop_consumers(self):
        """
        Stop consuming messages from AMQP broker
        :return:
        """
        self.comms.stop_receiving()

    def set_properties(self, reg_entity, properties):
        raise NotImplementedError

    def unregister(self, entity_obj):
        raise NotImplementedError

