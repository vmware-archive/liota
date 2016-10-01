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

from abc import ABCMeta, abstractmethod
from liota.entities.entity import Entity
from liota.dcc_comms.dcc_comms import DCCComms
from liota.entities.metrics.registered_metric import RegisteredMetric


class DataCenterComponent:

    """
    Abstract base class for all DCCs.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, comms):
        if not isinstance(comms, DCCComms):
            raise TypeError
        self.comms = comms

    # -----------------------------------------------------------------------
    # Implement this method in subclasses and do actual registration.
    #
    # This method should return a RegisteredEntity if successful, or raise
    # an exception if failed. Call this method from subclasses for a type
    # check.
    #

    @abstractmethod
    def register(self, entity_obj):
        if not isinstance(entity_obj, Entity):
            raise TypeError

    @abstractmethod
    def create_relationship(self, reg_entity_parent, reg_entity_child):
        pass

    @abstractmethod
    def _format_data(self, reg_metric):
        pass

    def publish(self, reg_metric):
        if not isinstance(reg_metric, RegisteredMetric):
            raise TypeError
        message = self._format_data(reg_metric)
        self.comms.send(message)

    @abstractmethod
    def set_properties(self, reg_entity, properties):
        pass

class RegistrationFailure(Exception): pass
