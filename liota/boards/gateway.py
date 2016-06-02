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
import logging
import time

from liota.transformers.metrics import Sample
from liota.utilities.utility import getUTCmillis


log = logging.getLogger(__name__)
class Gateway:
    __metaclass__ = ABCMeta
    """ The base class in order to define the various functions that
        are required in order to define Gateway object

    """
    def __init__(self, make, model, os, identifier, res_name, res_uuid, parent, type, res_kind):
        self.make = make
        self.model = model
        self.os = os
        self.identifier = identifier
        self.res_name = res_name
        self.res_uuid = res_uuid
        self.parent = parent
        self.type = type
        self.res_kind = res_kind
        self.property_key_value_map = {}
        # A single pin can report multiple metrics. Following map associates metrics with pins
        self.pin_to_metrics_map = {}
        self.pins = {}
        self._configure_pins()
        self._initialize_gateway()

    @abstractmethod
    def _configure_pins(self):
        pass

    @abstractmethod
    def _initialize_gateway(self):
        pass

    @abstractmethod
    def _report_data(self, msg_id, statkey, timestamps, values):
        return {
         "type": "add_stats",
         "uuid": self.res_uuid,
         "metric_data": [{
            "statKey": statkey,
            "timestamps": timestamps,
            "data": values
         }],
      }

    @abstractmethod
    def _create_relationship(self, msg_id, parent):
        return {
         "transactionID": msg_id,
         "type": "create_relationship_request",
         "body": {
            "parent": parent.res_uuid,
            "child": self.res_uuid
         }
      }
