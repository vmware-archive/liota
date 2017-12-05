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
from liota.lib.utilities.utility import read_user_config

dependencies = ["edge_systems/dell5k/edge_system"]


class PackageClass(LiotaPackage):
    """
    This package creates a AWSIoT DCC object and registers edge system on
    AWSIoT to acquire "registered edge system", i.e. aws_iot_edge_system.
    """

    def run(self, registry):
        """
        The execution function of a liota package.

        Establishes connection with AWSIoT DCC using MqttDccComms

        :param registry: the instance of ResourceRegistryPerPackage of the package
        :return:
        """
        import copy
        from liota.dccs.aws_iot import AWSIoT
        from liota.dcc_comms.mqtt_dcc_comms import MqttDccComms
        from liota.lib.transports.mqtt import QoSDetails
        from liota.lib.utilities.identity import Identity
        from liota.lib.utilities.tls_conf import TLSConf

        # Acquire resources from registry
        # Creating a copy of edge_system object to keep original object "clean"
        edge_system = copy.copy(registry.get("edge_system"))

        # Get values from configuration file
        config_path = registry.get("package_conf")
        config = read_user_config(config_path + '/sampleProp.conf')
        # Encapsulates Identity
        identity = Identity(root_ca_cert=config['broker_root_ca_cert'], username=None, password=None,
                            cert_file=config['edge_system_cert_file'], key_file=config['edge_system_key_file'])
        # Encapsulate TLS parameters
        tls_conf = TLSConf(config['cert_required'], config['tls_version'], config['cipher'])
        # Encapsulate QoS related parameters
        qos_details = QoSDetails(config['in_flight'], config['queue_size'], config['retry'])

        #  Connecting to AWSIoT
        #  Publish topic for all Metrics will be 'liota/generated_local_uuid_of_edge_system/request'
        #  Create and pass custom MqttMessagingAttributes object to MqttDccComms to have custom topic
        self.aws_iot = AWSIoT(MqttDccComms(edge_system_name=edge_system.name,
                                           url=config['BrokerIP'], port=config['BrokerPort'], identity=identity,
                                           tls_conf=tls_conf,
                                           qos_details=qos_details,
                                           clean_session=True,
                                           protocol=config['protocol'], transport=['transport'],
                                           conn_disconn_timeout=config['ConnectDisconnectTimeout']),
                              enclose_metadata=True)

        # Register edge system (gateway)
        aws_iot_edge_system = self.aws_iot.register(edge_system)

        registry.register("aws_iot", self.aws_iot)
        registry.register("aws_iot_edge_system", aws_iot_edge_system)

    def clean_up(self):
        """
        The clean up function of a liota package.

        Disconnects from AWSIoT DCC.

        :return:
        """
        self.aws_iot.comms.client.disconnect()
