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

dependencies = ["edge_systems/dell5k/edge_system"]


class PackageClass(LiotaPackage):
    """
    This package creates a AWSIoT DCC object and registers edge system on
    AWSIoT to acquire "registered edge system", i.e. aws_iot_edge_system.
    """

    def run(self, registry):
        import copy
        from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
        from liota.dccs.aws_iot import AWSIoT
        from liota.dcc_comms.aws_mqtt_dcc_comms import AWSMQTTDccComms

        # Acquire resources from registry
        # Creating a copy of edge_system object to keep original object "clean"
        edge_system = copy.copy(registry.get("edge_system"))

        # Get values from configuration file
        config_path = registry.get("package_conf")
        aws_conf = {}
        execfile(config_path + '/awsSampleProp.conf', aws_conf)

        #  These are standard steps to be followed to connect with AWS IoT using AWS IoT SDK
        mqtt_client = AWSIoTMQTTClient(aws_conf['GatewayName'])
        mqtt_client.configureEndpoint(aws_conf['AWSEndpoint'], aws_conf['AWSPort'])
        mqtt_client.configureCredentials(aws_conf['RootCAPath'], aws_conf['PrivateKeyPath'], aws_conf['ClientCertPath'])
        mqtt_client.configureConnectDisconnectTimeout(aws_conf['ConnectDisconnectTimeout'])
        mqtt_client.configureMQTTOperationTimeout(aws_conf['OperationTimeout'])

        #  Initializing AWSMQTTDccComms with AWSIoT client object
        #  Connecting to AWS
        #  Initializing AWS DCC using AWSMQTTDccComms object
        #  QoS is 1 and enclose_metadata is False by default
        self.aws_iot = AWSIoT(AWSMQTTDccComms(mqtt_client))

        # Register edge system (gateway)
        aws_iot_edge_system = self.aws_iot.register_entity(edge_system, None)

        registry.register("aws_iot", self.aws_iot)
        registry.register("aws_iot_edge_system", aws_iot_edge_system)

    def clean_up(self):
        self.aws_iot.comms._disconnect()
