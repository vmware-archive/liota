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
from abc import ABCMeta, abstractmethod

from liota.entities.entity import Entity
from liota.dcc_comms.dcc_comms import DCCComms
from liota.entities.metrics.registered_metric import RegisteredMetric

log = logging.getLogger(__name__)


class DataCenterComponent:

    """
    Abstract base class for all DCCs.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, comms):
        """
        Abstract init method for DCC (Data Center Component).

        :param comms: DccComms Object
        """
        if not isinstance(comms, DCCComms):
            log.error("DCCComms object is expected.")
            raise TypeError("DCCComms object is expected.")
        self.comms = comms

    @abstractmethod
    def register(self, entity_obj):
        """
        Abstract register method to register an Entity Object with the Dcc.  Call this method from subclasses for a type
        check.

        If successful RegisteredEntity should be returned by DCC implementation. Raise an exception if failed.

        :param entity_obj: Entity Object to be registered.
        :return:
        """
        if not isinstance(entity_obj, Entity):
            log.error("Entity object is expected.")
            raise TypeError("Entity object is expected.")

    @abstractmethod
    def create_relationship(self, reg_entity_parent, reg_entity_child):
        """
        Abstract create_relationship method to create a relationship between a parent and a child entity.

        :param reg_entity_parent: RegisteredEntity object of the parent.
        :param reg_entity_child:  RegisteredEntity object of the child.
        :return:
        """
        pass

    @abstractmethod
    def _format_data(self, reg_metric):
        """
        Abstract _format_data method.  This is a private method and it should take care of formatting the message
        in a structure specific to a DCC.

        :param reg_metric: RegisteredMetric Object
        :return: Formatted message string
        """
        pass

    def publish(self, reg_metric):
        """
        Publishes the formatted message to the Dcc using DccComms.

        Users must pass MessagingAttributes Object as part of RegisteredMetric Objects wherever necessary.

        This method EXPECTS MessagingAttributes to be passed in RegisteredMetric's 'msg_attr' attribute.

        :param reg_metric: RegisteredMetricObject.
        :return:
        """
        if not isinstance(reg_metric, RegisteredMetric):
            log.error("RegisteredMetric object is expected.")
            raise TypeError("RegisteredMetric object is expected.")
        message = self._format_data(reg_metric)
        if message:
            if hasattr(reg_metric, 'msg_attr'):
                self.comms.send(message, reg_metric.msg_attr)
            else:
                self.comms.send(message, None)

    @abstractmethod
    def set_properties(self, reg_entity, properties):
        """
        Abstract set_properties method.  DCCs should implement this method to allow RegisteredEntities to set their
        properties.

        :param reg_entity: RegisteredEntity Object
        :param properties: Property String, List or Dict dependant on DCC implementation
        :return:
        """
        pass

    @abstractmethod
    def unregister(self, entity_obj):
        """
        Abstract unregister method.  DCCs should implement this method to un-register an Entity.

        :param entity_obj: Entity Object
        :return:
        """
        if not isinstance(entity_obj, Entity):
            raise TypeError


class RegistrationFailure(Exception):
    """
    Raise this exception in case of registration failure with the DCC.
    """
    pass

