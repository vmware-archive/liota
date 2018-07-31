# ----------------------------------------------------------------------------#
#  Copyright © 2017-2018 VMware, Inc. All Rights Reserved.                    #
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
# -*- coding: utf-8 -*-
from liota.core.package_manager import LiotaPackage
from random import randint
import time
import socket
import logging
import random
import json
import httplib
from liota.lib.utilities.utility import systemUUID

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

#device name, you should register a device in edgexfoundry with this name
device_name = "GS1-AC-Drive01"
#device_metric_name , which refers to ValueDescriptor in edgexfoundry(or the property of DeviceProfile)
device_metric_name = "HoldingRegister_8455"

# ---------------------------------------------------------------------------
# This is a sample application package to publish sample device stats to
# IoTCC using MQTT protocol as DCC Comms
# User defined methods

def device_metric():
     #httpclient request for edgexfounry command-microservice to get device data.j
     conn = httplib.HTTPConnection('10.112.122.28',48082,timeout=5)
     conn.request('GET', '/api/v1/device/GS1-AC-Drive01/command/GS1-AC-Drive01')
     res = conn.getresponse()
     data = res.read()
     data_dict = json.loads(data)
     value = data_dict["HoldingRegister_8455"]
     return value

class PackageClass(LiotaPackage):
    def run(self, registry):
        """
        The execution function of a liota package.
        Acquires "iotcc_mqtt" and "iotcc_mqtt_edge_system" from registry then register five devices
        and publishes device metrics to the DCC
        :param registry: the instance of ResourceRegistryPerPackage of the package
        :return:
        """
        from liota.entities.devices.device import Device
        from liota.entities.metrics.metric import Metric
        import copy

	    log.info("-----------beging register device with:" + device_name + "--" +device_metric_name)
        # Acquire resources from registry
        self.iotcc = registry.get("iotcc_mqtt")
        # Creating a copy of edge_system object to keep original object "clean"
        self.iotcc_edge_system = copy.copy(registry.get("iotcc_mqtt_edge_system"))

        self.reg_devices = []
        self.metrics = []

        try:
            # Register device

            device = Device(device_name,systemUUID().get_uuid(device_name),"edgexfoundry")
            log.info("Registration Started for Device".format(device.name))

            # Device Registration

            reg_device = self.iotcc.register(device)

            self.reg_devices.append(reg_device)
            self.iotcc.create_relationship(self.iotcc_edge_system, reg_device)

            # Use the device name as identifier in the registry to easily refer the device in other packages
            device_registry_name = device_name
            registry.register(device_registry_name, reg_device)
	        log.info("----------------relation success:"+str(device_name)+"----------------------")
            self.iotcc.set_properties(reg_device,
                                              {"Country": "USA-G", "State": "California", "City": "Palo Alto",
                                               "Location": "VMware HQ", "Building": "Promontory H Lab",
                                               "Floor": "First Floor"})

            try:
                # Registering Metric for Device
                metric_name = device_metric_name + "_metrics"

                metric_simulated_received = Metric(name=metric_name, unit=None, interval=5,
                                                   aggregation_size=1, sampling_function=device_metric)
                reg_metric_simulated_received = self.iotcc.register(metric_simulated_received)
                self.iotcc.create_relationship(reg_device, reg_metric_simulated_received)
                reg_metric_simulated_received.start_collecting()
		        log.info("--------------relation metics:"+device_metric_name+"----------------------")
                self.metrics.append(reg_metric_simulated_received)

            except Exception as e:
                log.error(
                    'Exception while lioading metric {0} for device {1} - {2}'.format(metric_name, device.name,
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
