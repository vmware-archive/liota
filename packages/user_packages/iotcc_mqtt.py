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

dependencies = ["general_edge_system", "credentials"]


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
        import time
        from liota.lib.utilities.identity import Identity
        from liota.dccs.iotcc import IotControlCenter
        from liota.dcc_comms.mqtt_dcc_comms import MqttDccComms
        from liota.lib.transports.mqtt import MqttMessagingAttributes
        from liota.dccs.dcc import RegistrationFailure
        from liota.lib.utilities.tls_conf import TLSConf

        # Acquire resources from the registry
        # Creating a copy of edge_system object to keep original object "clean"
        edge_system = copy.copy(registry.get("edge_system"))

        #  Encapsulates Identity
        # Acquire credentials and required certificates from the registry
        identity = Identity(root_ca_cert=registry.get("broker_root_ca_cert"), username=registry.get("broker_username"),
                            password=registry.get("broker_password"),
                            cert_file=registry.get("edge_system_cert_file"), key_file=registry.get("edge_system_key_file"))

        # Encapsulate TLS parameters
        tls_conf = TLSConf(cert_required="CERT_REQUIRED", tls_version="PROTOCOL_TLSv1_2", cipher=None)

        # Initialize DCC object with MQTT transport
        mqtt_msg_attr = MqttMessagingAttributes(pub_topic="liota/"+registry.get("broker_username")+"/request",sub_topic="liota/"+registry.get("broker_username")+"/response")
        self.iotcc = IotControlCenter(MqttDccComms(edge_system_name=edge_system.name,
                                              url=registry.get("broker_ip"), port=registry.get("broker_port"), identity=identity,
                                              tls_conf=tls_conf,client_id=registry.get("broker_username"),
                                              enable_authentication=True, mqtt_msg_attr=mqtt_msg_attr))

        try:
            # Register edge system (gateway)
            self.iotcc_edge_system = self.iotcc.register(edge_system)
            # System Properties has to be set only for the registered edge system before it is stored in the package
            # manager registry, all the devices will internally inherit the the system properties from the
            # registered edge system
            self.iotcc.set_system_properties(self.iotcc_edge_system, registry.get("system_properties"))
            # Set the properties for edge system as key:value pair, you can also set the location
            # by passing the latitude and longitude as a property in the user package
            # If the set_properties or register call fails due to DCC_Comms Publish exception
            # the optional retry mechanism can be implemented in the following way
            attempts = 0
            while attempts < 3:
                try:
                    # Register edge system (gateway)
                    self.iotcc.set_properties(self.iotcc_edge_system, {"key1": "value1", "key2": "value2"})
                    break
                except Exception:
                    attempts += 1
                    # The sleep time before re-trying depends on the infrastructure requirement of broker to restart
                    # It can be modified or removed as per the infrastructure requirement
                    time.sleep(5)
            registry.register("iotcc_mqtt", self.iotcc)
            # Store the registered edge system object in liota package manager registry after the
            # system properties are set for it
            registry.register("iotcc_mqtt_edge_system", self.iotcc_edge_system)

        except RegistrationFailure:
            print "EdgeSystem registration to IOTCC failed"

    def clean_up(self):
        """
        The clean up function of a liota package.

        Disconnects from IoTControlCenter DCC and un-registers the edge-system.

        :return:
        """
        # Unregister the edge system on package unload
        # Kindly include the edge system un-register call on package unload
        self.iotcc.unregister(self.iotcc_edge_system)
        self.iotcc.comms.client.disconnect()
