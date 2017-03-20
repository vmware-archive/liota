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
from liota.lib.utilities.utility import read_liota_config
import json

dependencies = ["iotcc"]


class PackageClass(LiotaPackage):
    def run(self, registry):
        # Acquire resources from registry
        iotcc = registry.get("iotcc")

        # Get values from configuration file
        iotcc_json_path = read_liota_config('IOTCC_PATH', 'iotcc_path')
        if iotcc_json_path == '':
            return
        try:
            with open(iotcc_json_path, 'r') as f:
                iotcc_details_json_obj = json.load(f)["iotcc"]
            f.close()
        except IOError, err:
            return

        organization_group_properties = iotcc_details_json_obj["OGProperties"]

        edge_system = iotcc_details_json_obj["EdgeSystem"]

        # Set organization group property for edge_system
        iotcc.set_organization_group_properties(edge_system["SystemName"], edge_system["uuid"], edge_system["EntityType"],
                                                organization_group_properties)

        for device in iotcc_details_json_obj['Devices']:
            # Set Organization group property for devices
            iotcc.set_organization_group_properties(device["DeviceName"], device["uuid"], device["EntityType"],
                                                    organization_group_properties)

    def clean_up(self):
        pass
