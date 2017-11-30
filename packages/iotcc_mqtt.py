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
    This is a sample package which creates a IoTControlCenter DCC object and registers edge system on
    IoTCC over MQTT Protocol to acquire "registered edge system", i.e. iotcc_edge_system.
    """

    def run(self, registry):
        """
        The execution function of a liota package.

        Establishes connection with IoTControlCenter DCC using MqttDccComms

        :param registry: the instance of ResourceRegistryPerPackage of the package
        :return:
        """
        import copy
        from liota.lib.utilities.identity import Identity
        from liota.dccs.iotcc import IotControlCenter
        from liota.dcc_comms.mqtt_dcc_comms import MqttDccComms
        from liota.dccs.dcc import RegistrationFailure
        from liota.lib.utilities.tls_conf import TLSConf

        # Get values from configuration file
        self.config_path = registry.get("package_conf")
        config = read_user_config(self.config_path + '/sampleProp.conf')

        # Acquire resources from registry
        # Creating a copy of edge_system object to keep original object "clean"
        edge_system = copy.copy(registry.get("edge_system"))

        #  Encapsulates Identity
        identity = Identity(root_ca_cert=config['broker_root_ca_cert'], username=config['broker_username'],
                            password=config['broker_password'],
                            cert_file=config['edge_system_cert_file'], key_file=config['edge_system_key_file'])

        # Encapsulate TLS parameters
        tls_conf = TLSConf(config['cert_required'], config['tls_version'], config['cipher'])

        # Initialize DCC object with MQTT transport
        self.iotcc = IotControlCenter(MqttDccComms(edge_system_name=edge_system.name,
                                              url=config['BrokerIP'], port=config['BrokerPort'], identity=identity,
                                              tls_conf=tls_conf,
                                              enable_authentication=True))

        try:
            # Register edge system (gateway)
            self.iotcc_edge_system = self.iotcc.register(edge_system)
            """
            Use iotcc & iotcc_edge_system as common identifiers
            in the registry to easily refer the objects in other packages
            """
            registry.register("iotcc_mqtt", self.iotcc)
            registry.register("iotcc_mqtt_edge_system", self.iotcc_edge_system)
        except RegistrationFailure:
            print "EdgeSystem registration to IOTCC failed"
        self.iotcc.set_properties(self.iotcc_edge_system, config['SystemPropList'])

    def clean_up(self):
        """
        The clean up function of a liota package.

        Disconnects from IoTControlCenter DCC and un-registers the edge-system if specified in configuration.

        :return:
        """
        # Get values from configuration file
        config = read_user_config(self.config_path + '/sampleProp.conf')

        # Un-register edge system
        if config['ShouldUnregisterOnUnload'] == "True":
            self.iotcc.unregister(self.iotcc_edge_system)
        self.iotcc.comms.client.disconnect()
