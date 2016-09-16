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

dependencies = ["gateway"]

class PackageClass(LiotaPackage):
    """
    This package creates a vROps DCC object and registers gateway on vROps
    to acquire "registered gateway", i.e. vrops_gateway.
    """

    def run(self, registry):
        import copy
        from liota.dcc.vrops import Vrops
        from liota.transports.web_socket import WebSocket

        # Acquire resources from registry
        # Creating a copy of gateway object to keep original object "clean"
        gateway = copy.copy(registry.get("gateway"))

        # Get values from configuration file
        config = {}
        config_path = registry.get("package_conf")
        execfile(config_path + "/sampleProp.conf", config)

        # Initialize DCC object with transport
        self.vrops = Vrops(
                config['vROpsUID'],
                config['vROpsPass'],
                WebSocket(url=config['WebSocketUrl'])
            )

        # Register gateway
        vrops_gateway = self.vrops.register(gateway)
        assert(vrops_gateway.registered)
        self.vrops.set_properties(vrops_gateway, config['Gateway1PropList'])
        
        registry.register("vrops", self.vrops)
        registry.register("vrops_gateway", vrops_gateway)

    def clean_up(self):
        self.vrops.con.close()
