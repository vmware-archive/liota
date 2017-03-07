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

from liota.dccs.basic_dcc import BasicDataCenterComponent

log = logging.getLogger(__name__)


class AWSIoT(BasicDataCenterComponent):
    """
    DCC for AWSIoT Platform.
    """
    def __init__(self, con, enclose_metadata=False):
        """
        :param con: DccComms Object
        :param enclose_metadata: Include Gateway, Device and Metric names as part of payload or not
        """
        super(AWSIoT, self).__init__(
            comms=con,
            enclose_metadata=enclose_metadata
        )

    def register(self, entity_obj):
        """
        :param entity_obj: Entity Object
        :return: RegisteredEntity Object
        """
        log.info("Registering resource with AWSIoT DCC {0}".format(entity_obj.name))
        return super(AWSIoT, self).register(entity_obj)

    def create_relationship(self, reg_entity_parent, reg_entity_child):
        """
        :param reg_entity_parent: Registered EdgeSystem or Registered Device Object
        :param reg_entity_child:  Registered Device or Registered Metric Object
        :return: None
        """
        super(AWSIoT, self).create_relationship(reg_entity_parent, reg_entity_child)

    def _format_data(self, reg_metric):
        """
        :param reg_metric: Registered Metric Object
        :return: Payload in JSON format
        """
        return super(AWSIoT, self)._format_data(reg_metric)

    def set_properties(self, reg_entity, properties):
        raise NotImplementedError
