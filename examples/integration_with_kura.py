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


import logging
import json
import time
import threading
import random
import copy
from liota.entities.devices.simulated_device import SimulatedDevice
from liota.entities.metrics.metric import Metric
from liota.device_comms.mqtt_device_comms import MqttDeviceComms
from liota.core.package_manager import LiotaPackage
from liota.lib.utilities.utility import get_default_network_interface, get_disk_name


log = logging.getLogger(__name__)
dependencies = ["iotcc_mqtt"]
network_interface = get_default_network_interface()
disk_name = get_disk_name()
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

lock = threading.Lock()
Msg_dic = {}                #{"demo": {"flag": 0, "msg": 0, "metric": metric}}
Gatewaydict = {}            #{"assetName": reg_device}

callbackFunc_str = '''def metric_callback_%s():    return Msg_dic['%s']['msg']'''

class PackageClass(LiotaPackage):

    BrokerIP = "127.0.0.1"
    BrokerPort = 1883
    BrokerTopic = "#"
    metrics = []
    reg_devices = []

    """Subscibe callback function"""
    def sub_callback(self, client, userdata, msg):

        if (msg.topic.split("/").__len__() == 4) and (msg.topic.split("/")[3] == "pulse-topic"):

            Jsonpayload = json.loads(msg.payload)['metrics']
            if Jsonpayload:

                #is new gateway?
                if Jsonpayload['assetName'] in Gatewaydict.keys():

                    log.info("is old gateway")

                    for key_metric in Jsonpayload.keys():

                        # filter the unuseful sensor
                        if key_metric == "assetName":
                            continue
                        if key_metric.find('stamp') >= 0:
                            continue

                        if key_metric in Msg_dic.keys(): #exist update msg

                            Msg_dic[key_metric]['msg'] = Jsonpayload[key_metric]
                            Msg_dic[key_metric]['flag'] = 0

                        else:

                            Msg_dic[key_metric] = {}
                            Msg_dic[key_metric]['msg'] = Jsonpayload[key_metric]
                            Msg_dic[key_metric]['flag'] = 1

                            exec(callbackFunc_str % (key_metric, key_metric))

                            try:
                                metric_ins = Metric(name=key_metric,
                                                    unit=None, interval=3,
                                                    aggregation_size=1,
                                                    sampling_function=eval("metric_callback_%s" % key_metric)
                                                    )
                                reg_metric = userdata['self'].iotcc.register(metric_ins)
                                userdata['self'].iotcc.create_relationship(Gatewaydict[Jsonpayload['assetName']], reg_metric)
                                reg_metric.start_collecting()
                                userdata['self'].metrics.append(reg_metric)
                                Msg_dic[key_metric]['metric'] = reg_metric

                            except Exception as e:
                                log.error(
                                    'Exception while loading metric {0} for Edge System {1}'.format
                                    (key_metric, str(e)))


                else: #new device enrolling

                    log.info("is new gateway")

                    try:
                        # Register device
                        device = SimulatedDevice(Jsonpayload['assetName'], Jsonpayload['assetName'])
                        # Device Registration attempts
                        reg_attempts = 0
                        # Started Device Registration attempts
                        while reg_attempts <= retry_attempts:
                            try:
                                reg_device = userdata['self'].iotcc.register(device)
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

                        userdata['self'].reg_devices.append(reg_device)

                        # Attempts to set device relationship with edge system
                        relationship_attempts = 0
                        while relationship_attempts <= retry_attempts:
                            try:
                                userdata['self'].iotcc.create_relationship(userdata['self'].iotcc_edge_system, reg_device)
                                break
                            except Exception as e:
                                if relationship_attempts == retry_attempts:
                                    raise
                                relationship_attempts += 1
                                log.error(
                                    'Trying Device {0} relationship with Edge System failed with following error - {1}'
                                        .format(device.name, str(e)))
                                log.info(
                                    '{0} Device Relationship: Attempt: {1}'.format(device.name, str(relationship_attempts)))
                                time.sleep(delay_retries)

                        # Use the device name as identifier in the registry to easily refer the device in other packages
                        device_registry_name = Jsonpayload['assetName']

                        userdata['registry'].register(device_registry_name, reg_device)

                        # Setting multiple properties by passing Dictonary object for Devices with the retry attempts
                        # in case of exceptions
                        prop_attempts = 0
                        while prop_attempts <= retry_attempts:
                            try:
                                userdata['self'].iotcc.set_properties(reg_device,
                                                          {"Country": "CN-B", "State": "BeiJing", "City": "China",
                                                           "Location": "VMware BeiJing", "Building": "BeiJing",
                                                           "Floor": "BeiJing Floor"})
                                break

                            except Exception as e:
                                prop_attempts = prop_attempts + 1
                                log.error('Exception while setting property for Device {0} - {1}'
                                    .format(device.name, str(e)))
                                log.info('Trying setting properties for Device {0}: Attempt - {1}'
                                         .format(device.name,str(prop_attempts)))
                                time.sleep(delay_retries)

                    except Exception:
                        log.info("Device Registration and Metrics loading failed")
                        self.clean_up()
                        raise

                    Gatewaydict[Jsonpayload['assetName']] = reg_device
            else:
                log.info("Jsonpayload empty")
        else:
            log.info("another topic")


    def run(self, registry):
        """
        The execution function of a liota package.

        Acquires "iotcc_mqtt" and "iotcc_mqtt_edge_system" from registry and registers edge_system related metrics
        with the DCC and publishes those metrics.

        :param registry: the instance of ResourceRegistryPerPackage of the package
        :return:
        """
        self.iotcc = registry.get("iotcc_mqtt")
        self.iotcc_edge_system = copy.copy(registry.get("iotcc_mqtt_edge_system"))

        self.mqtt_dev_comms = MqttDeviceComms(self.BrokerIP, self.BrokerPort,
                                              identity=None,
                                              tls_conf=None, qos_details=None,
                                              client_id="pulse", clean_session=True,
                                              userdata={"self": self, "registry": registry},
                                              protocol="MQTTv311", transport="tcp",
                                              keep_alive=60, enable_authentication=False, conn_disconn_timeout=10)

        self.mqtt_dev_comms.subscribe(self.BrokerTopic, 0, self.sub_callback)

    def clean_up(self):
        """
        The clean up function of a liota package.

        Stops metric collection and publish.
        :return:
        """
        # Kindly include this call to stop the metrics collection on package unload

        try:
            for metric in self.metrics:
                metric.stop_collecting()
        except Exception:
            log.info("Stop collecting failed.")
            raise

        try:
            for device in self.reg_devices:
                self.iotcc.unregister(device)
        except Exception:
            log.info("Unregister devices failed.")
            raise

        try:
            self.mqtt_dev_comms._disconnect()
        except Exception:
            log.info("Disconnect failed.")
            raise
