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
import time
import logging
import random

log = logging.getLogger(__name__)

dependencies = ["general_edge_system", "credentials"]

# --------------------User Configurable Retry and Delay Settings------------------------------#

# The value mentioned below is the total number of Edge System being deployed in the infrastructure
# minimum 1 for 1K, 2 for 2K, 3 for 3K, 4 for 4K and  5 for 5K Edge Systems
no_of_edge_system_in_thousands = 1
# Number of Retries for Connection and Registrations
no_of_retries_for_connection = 5
# MQTT Connection Delay Min Value in seconds
mqtt_connection_retry_delay_min = 10
# MQTT Connection Delay Max Value in seconds
mqtt_connection_retry_delay_max = 600
# Retry delay Min Value in seconds
delay_retries_min = 600
# Retry delay Max Value in seconds
retries_delay_max = 1800

# Lambda Function Multiplier uses the above settings for calculating retry and delay logic
lfm = lambda x: x * no_of_edge_system_in_thousands
retry_attempts = lfm(no_of_retries_for_connection)
mqtt_connection_delay_retries = random.randint(lfm(mqtt_connection_retry_delay_min),
                                               lfm(mqtt_connection_retry_delay_max))
delay_retries = random.randint(lfm(delay_retries_min), lfm(retries_delay_max))


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
        from liota.lib.transports.mqtt import MqttMessagingAttributes
        from liota.lib.utilities.tls_conf import TLSConf

        # Acquire resources from the registry
        # Creating a copy of edge_system object to keep original object "clean"
        edge_system = copy.copy(registry.get("edge_system"))

        #  Encapsulates Identity
        # Acquire credentials and required certificates from the registry
        identity = Identity(root_ca_cert=registry.get("broker_root_ca_cert"), username=registry.get("broker_username"),
                            password=registry.get("broker_password"),
                            cert_file=registry.get("edge_system_cert_file"),
                            key_file=registry.get("edge_system_key_file"))

        # Encapsulate TLS parameters
        tls_conf = TLSConf(cert_required="CERT_REQUIRED", tls_version="PROTOCOL_TLSv1_2", cipher=None)

        # Initialize DCC object with MQTT transport
        mqtt_msg_attr = MqttMessagingAttributes(pub_topic="liota/" + registry.get("broker_username") + "/request",
                                                sub_topic="liota/" + registry.get("broker_username") + "/response")

        # Attempts for establishing MQTT Connection
        conn_attempts = 0

        try:
            # Trying to establish MQTT Connection with retry attempts in case of exception
            while conn_attempts <= retry_attempts:
                try:
                    self.iotcc = IotControlCenter(
                        MqttDccComms(edge_system_name=edge_system.name, url=registry.get("broker_ip"),
                                     port=registry.get("broker_port"), identity=identity, tls_conf=tls_conf,
                                     client_id=registry.get("broker_username"), enable_authentication=True,
                                     mqtt_msg_attr=mqtt_msg_attr))
                    break
                except Exception as e:
                    if conn_attempts == retry_attempts:
                        raise
                    conn_attempts += 1
                    log.error('MQTT Connection failed - {0}'.format(str(e)))
                    log.info('Trying MQTT Connection: Attempt - {0}'.format(str(conn_attempts)))
                    time.sleep(mqtt_connection_delay_retries)

            # Attempts for Edge System Registration
            reg_attempts = 0
            # Edge System Registration with retry attempts in case of exception
            while reg_attempts <= retry_attempts:
                try:
                    self.iotcc_edge_system = self.iotcc.register(edge_system)
                    break
                except Exception as e:
                    if reg_attempts == retry_attempts:
                        raise
                    reg_attempts += 1
                    log.error('Exception while registering Edge System- {0}'.format(str(e)))
                    log.info('Trying Edge System {0} Registration: Attempt - {1}'.format(edge_system.name,
                                                                                         str(reg_attempts)))
                    time.sleep(delay_retries)

            registry.register("iotcc_mqtt", self.iotcc)
            registry.register("iotcc_mqtt_edge_system", self.iotcc_edge_system)

            # Attempts for setting edge system properties
            prop_attempts = 0
            # Set multiple properties by passing Dictonary object for Edge System with the retry attempts
            # in case of exceptions
            while prop_attempts < retry_attempts:
                try:
                    self.iotcc.set_properties(self.iotcc_edge_system,
                                              {"Country": "USA-G", "State": "California", "City": "Palo Alto",
                                               "Location": "VMware HQ", "Building": "Promontory H Lab",
                                               "Floor": "First Floor"})
                    break
                except Exception as e:
                    prop_attempts += 1
                    log.error(
                        'Exception while setting Property for Edge System {0} - {1}'.format(edge_system.name, str(e)))
                    log.info('Trying setting properties for Edge System {0}: Attempt - {1}'.format(edge_system.name,
                                                                                                   str(prop_attempts)))
                    time.sleep(delay_retries)

        except Exception:
            log.error("EdgeSystem registration to IOTCC failed even after all the retries, starting connection cleanup")
            # Disconnecting MQTT
            self.iotcc.comms.client.disconnect()
            raise

    def clean_up(self):
        # Unregister the edge system
        # On the unload of the package the Edge System will get unregistered and the entire history will be deleted
        # from Pulse IoT Control Center so comment the below logic if the unregsitration of the device is not required
        # to be done on the package unload
        self.iotcc.unregister(self.iotcc_edge_system)
        # Disconnecting MQTT
        self.iotcc.comms.client.disconnect()
        log.info("Cleanup completed successfully")
