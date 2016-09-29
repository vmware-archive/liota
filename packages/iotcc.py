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

from liota.core.package_manager import LiotaPackage

dependencies = ["edgesystems/dell5k/edgesystem"]


class PackageClass(LiotaPackage):
    """
    This package creates a IoTControlCenter DCC object and registers edgesystem on
    IoTCC to acquire "registered edgesystem", i.e. iotcc_edgesystem.
    """

    def run(self, registry):
        import copy
        from liota.dccs.iotcc import IotControlCenter
        from liota.dcc_comms.websocket_dcc_comms import WebSocketDccComms

        # Acquire resources from registry
        # Creating a copy of edgesystem object to keep original object "clean"
        edgesystem = copy.copy(registry.get("edgesystem"))

        # Get values from configuration file
        config_path = registry.get("package_conf")
        config = {}
        execfile(config_path + '/sampleProp.conf', config)

        # Initialize DCC object with transport
        self.iotcc = IotControlCenter(
            config['IotCCUID'], config['IotCCPassword'],
            WebSocketDccComms(url=config['WebSocketUrl'])
        )

        # Register gateway system
        iotcc_edgesystem = self.iotcc.register(edgesystem)

        registry.register("iotcc", self.iotcc)
        registry.register("iotcc_edgesystem", iotcc_edgesystem)

    def clean_up(self):
        self.iotcc.comms.wss.close()
