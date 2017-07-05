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

import Queue

import pint

from liota.dcc_comms.websocket_dcc_comms import WebSocketDccComms
from liota.dccs.dcc import RegistrationFailure
from liota.dccs.iotcc import IotControlCenter
from liota.device_comms.mqtt_device_comms import MqttDeviceComms
from liota.entities.devices.simulated_device import SimulatedDevice
from liota.entities.edge_systems.dk300_edge_system import Dk300EdgeSystem
from liota.entities.metrics.metric import Metric
from liota.lib.utilities.identity import Identity
from liota.lib.utilities.tls_conf import TLSConf
from liota.lib.utilities.utility import read_user_config

# getting values from conf file
config = read_user_config('samplePropMqtt.conf')

# Create unit registry
ureg = pint.UnitRegistry()

# Store temperature values in Queue
kitchen_temperature_data = Queue.Queue()
living_room_temperature_data = Queue.Queue()


# Callback functions
# To put corresponding values in queue
def callback_kitchen_temp(client, userdata, message):
    kitchen_temperature_data.put(float(message.payload))


def callback_living_room_temp(client, userdata, message):
    living_room_temperature_data.put(float(message.payload))


# Extract data from Queue
def get_value(queue):
    return queue.get(block=True)


# ---------------------------------------------------------------------------------
# In this example, we demonstrate how data from two different Mqtt Channels (topics)
# can be collected and sent to IoTCC Dcc using Liota.
#
#
#                               IoTCC DCC
#                                  /|\
#                                   |
#                                   |
#                                   |  WebSocket
#                                   |
#                                   |
#                            Dell5kEdgeSystem
#                              /|\       /|\
#                               |         |
#             mqtt subscribe    |         |   mqtt subscribe
#          (temperature/kitchen)|         | (temperature/living-room)
#                               |         |
#                       --------------------------
#                      |                          |
#                      |        MQTT Broker       |
#                       --------------------------
#                       /|\                    /|\
#                        |                      |
#          mqtt publish  |                      |  mqtt publish
#  (temperature/kitchen) |                      | (temperature/living-room)
#                        |                      |
#                 Temperature Sensor       Temperature Sensor
#                   at Kitchen                at Living room
#
#
# Data streaming can be done from MQTT channel to IoTCC using LIOTA setting
# sampling_interval_sec to zero.
#
# Temperature values from sensor will be collected using MQTT channel and redirected
# to IoTCC data center component
# ------------------------------------------------------------------------------------


# MQTT connection setup to record kitchen and living room temperature values
def mqtt_subscribe():
    # Encapsulates Identity
    identity = Identity(config['broker_root_ca_cert'], config['broker_username'], config['broker_password'],
                        config['edge_system_cert_file'], config['edge_system_key_file'])
    # Encapsulate TLS parameters
    tls_conf = TLSConf(cert_required=config['cert_required'], tls_version=config['tls_version'],
                       cipher=config['cipher'])

    # Create MQTT connection object with required params
    mqtt_conn = MqttDeviceComms(url=config['BrokerIP'], port=config['BrokerPort'], identity=identity,
                                tls_conf=tls_conf,
                                qos_details=None,
                                clean_session=True,
                                keep_alive=config['keep_alive'], enable_authentication=True)

    # Subscribe to channels : "temperature/kitchen" and "temperature/living-room" with preferred QoS level 0, 1 or 2
    # Provide callback function as a parameter for corresponding channel
    mqtt_conn.subscribe(config['MqttChannel1'], 1, callback_kitchen_temp)
    mqtt_conn.subscribe(config['MqttChannel2'], 1, callback_living_room_temp)


if __name__ == "__main__":

    #  Creating EdgeSystem
    edge_system = Dk300EdgeSystem(config['EdgeSystemName'])

    # Connect with MQTT broker using DeviceComms and subscribe to topics
    # Get kitchen and living room temperature values using MQTT channel
    mqtt_subscribe()

    # Create DCC object IoTCC using websocket transport
    # with UID and PASS
    ws_identity = Identity(root_ca_cert=config['WebsocketCaCertFile'], username=config['IotCCUID'],
                           password=config['IotCCPassword'],
                           cert_file=config['ClientCertFile'], key_file=config['ClientKeyFile'])

    # Initialize DCC object with transport
    iotcc = IotControlCenter(
        WebSocketDccComms(url=config['WebSocketUrl'], verify_cert=config['VerifyServerCert'], identity=ws_identity)
    )

    try:

        # Register Edge System with IoT control center
        reg_edge_system = iotcc.register(edge_system)

        # these call set properties on the Resource representing the IoT System
        # properties are a key:value store
        reg_edge_system.set_properties(config['SystemPropList'])

        # Create kitchen device object and register it on IoTCC
        # Add two device names in the configurations as DeviceName1 and DeviceName2
        kitchen_temperature_device = SimulatedDevice(name=config['DeviceName1'])
        reg_kitchen_temperature_device = iotcc.register(kitchen_temperature_device)

        iotcc.create_relationship(reg_edge_system, reg_kitchen_temperature_device)
        reg_kitchen_temperature_device.set_properties(config['DevicePropList'])

        # Metric Name
        metric_name_kitchen_temperature = "temperature.kitchen"

        # Create metric for kitchen temperature
        kitchen_temperature = Metric(
            name=metric_name_kitchen_temperature,
            unit=ureg.degC,
            interval=0,
            sampling_function=lambda: get_value(kitchen_temperature_data)
        )

        reg_kitchen_temp = iotcc.register(kitchen_temperature)
        iotcc.create_relationship(reg_kitchen_temperature_device, reg_kitchen_temp)
        reg_kitchen_temp.start_collecting()

        # Create living room device object and register it on IoTCC
        living_room_temperature_device = SimulatedDevice(name=config['DeviceName2'])
        reg_living_room_temperature_device = iotcc.register(living_room_temperature_device)

        iotcc.create_relationship(reg_edge_system, reg_living_room_temperature_device)
        reg_living_room_temperature_device.set_properties(config['DevicePropList'])

        # Metric Name
        metric_name_living_room_temperature = "temperature.living"

        # Create metric for living room temperature
        living_room_temperature = Metric(
            name=metric_name_living_room_temperature,
            unit=ureg.degC,
            interval=0,
            sampling_function=lambda: get_value(living_room_temperature_data)
        )

        reg_living_room_temp = iotcc.register(living_room_temperature)
        iotcc.create_relationship(reg_living_room_temperature_device, reg_living_room_temp)
        reg_living_room_temp.start_collecting()

    except RegistrationFailure:
        print "Registration to IOTCC failed"
