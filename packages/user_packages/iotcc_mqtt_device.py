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
from random import randint
import time
import socket
import logging
import random

log = logging.getLogger(__name__)

dependencies = ["iotcc_mqtt"]

# --------------------User Configurable Retry and Delay Settings------------------------------#

# The value mentioned below is the total number of Edge System being deployed in the infrastructure
# minimum 1 for 1K, 2 for 2K, 3 for 3K, 4 for 4K and  5 for 5K Edge Systems
no_of_edge_system_in_thousands = 1
# Number of Retries for Connection and Registrations
no_of_retries_for_connection = 5
# Retry delay Min Value in seconds
delay_retries_min = 600
# Retry delay Max Value in seconds
delay_retries_max = 1800

# Lambda Function Multiplier uses the above settings for calculating retry and delay logic
lfm = lambda x: x * no_of_edge_system_in_thousands
retry_attempts = lfm(no_of_retries_for_connection)
delay_retries = random.randint(lfm(delay_retries_min), lfm(delay_retries_max))


# ---------------------------------------------------------------------------
# This is a sample application package to publish sample device stats to
# IoTCC using MQTT protocol as DCC Comms
# User defined methods

def device_metric():
    """
    This UDM randomly return values in between 0 to 999 in order to simulate device metric
    Use case specific device metric collection logic should be provided by user
    :return:
    """
    return randint(0, 999)


class PackageClass(LiotaPackage):
    def run(self, registry):
        """
        The execution function of a liota package.
        Acquires "iotcc_mqtt" and "iotcc_mqtt_edge_system" from registry then register five devices
        and publishes device metrics to the DCC
        :param registry: the instance of ResourceRegistryPerPackage of the package
        :return:
        """
        from liota.entities.devices.simulated_device import SimulatedDevice
        from liota.entities.metrics.metric import Metric
        import copy

        # Acquire resources from registry
        self.iotcc = registry.get("iotcc_mqtt")
        # Creating a copy of edge_system object to keep original object "clean"
        self.iotcc_edge_system = copy.copy(registry.get("iotcc_mqtt_edge_system"))

        self.reg_devices = []
        self.metrics = []
        num_devices = 5

        for i in range(0, num_devices):
            try:
                # Register device
                device = SimulatedDevice(socket.gethostname() + "-ChildDev" + str(i))
                log.info("Registration Started for Device {0}".format(device.name))
                # Device Registration attempts
                reg_attempts = 0
                # Started Device Registration attempts
                while reg_attempts <= retry_attempts:
                    try:
                        reg_device = self.iotcc.register(device)
                        break
                    except Exception as e:
                        if reg_attempts == retry_attempts:
                            raise
                        reg_attempts += 1
                        log.error(
                            'Trying Device {0} Registration failed with following error - {1}'.format(device.name,
                                                                                                      str(e)))
                        log.info('{0} Device Registration: Attempt: {1}'.format(device.name, str(reg_attempts)))
                        time.sleep(delay_retries)

                self.reg_devices.append(reg_device)
                # Attempts to set device relationship with edge system
                relationship_attempts = 0
                while relationship_attempts <= retry_attempts:
                    try:
                        self.iotcc.create_relationship(self.iotcc_edge_system, reg_device)
                        break
                    except Exception as e:
                        if relationship_attempts == retry_attempts:
                            raise
                        relationship_attempts += 1
                        log.error(
                            'Trying Device {0} relationship with Edge System failed with following error - {1}'.format(
                                device.name, str(e)))
                        log.info(
                            '{0} Device Relationship: Attempt: {1}'.format(device.name, str(relationship_attempts)))
                        time.sleep(delay_retries)
                # Use the device name as identifier in the registry to easily refer the device in other packages
                device_registry_name = socket.gethostname() + "-ChildDev" + str(i)
                registry.register(device_registry_name, reg_device)

                # Setting multiple properties by passing Dictonary object for Devices with the retry attempts
                # in case of exceptions
                prop_attempts = 0
                while prop_attempts <= retry_attempts:
                    try:
                        self.iotcc.set_properties(reg_device,
                                                  {"Country": "USA-G", "State": "California", "City": "Palo Alto",
                                                   "Location": "VMware HQ", "Building": "Promontory H Lab",
                                                   "Floor": "First Floor"})
                        break
                    except Exception as e:
                        prop_attempts = prop_attempts + 1
                        log.error('Exception while setting property for Device {0} - {1}'.format(
                            (device.name, str(e))))
                        log.info('Trying setting properties for Device {0}: Attempt - {1}'.format(device.name,
                                                                                                  str(prop_attempts)))
                        time.sleep(delay_retries)

                try:
                    # Registering Metric for Device
                    metric_name = "Simulated Metrics"
                    metric_simulated_received = Metric(name=metric_name, unit=None, interval=300,
                                                       aggregation_size=1, sampling_function=device_metric)
                    reg_metric_simulated_received = self.iotcc.register(metric_simulated_received)
                    self.iotcc.create_relationship(reg_device, reg_metric_simulated_received)
                    reg_metric_simulated_received.start_collecting()
                    self.metrics.append(reg_metric_simulated_received)
                except Exception as e:
                    log.error(
                        'Exception while loading metric {0} for device {1} - {2}'.format(metric_name, device.name,
                                                                                         str(e)))

            except Exception:
                log.info("Device Registration and Metrics loading failed")
                raise

    def clean_up(self):
        """
        The clean up function of a liota package.
        Unregister Device and Stops metric collection
        :return:
        """
        # On the unload of the package the device will get unregistered and the entire history will be deleted
        # from Pulse IoT Control Center so comment the below logic if the unregsitration of the device is not required
        # to be done on the package unload
        for metric in self.metrics:
            metric.stop_collecting()
        for device in self.reg_devices:
            self.iotcc.unregister(device)
        log.info("Cleanup completed successfully")
