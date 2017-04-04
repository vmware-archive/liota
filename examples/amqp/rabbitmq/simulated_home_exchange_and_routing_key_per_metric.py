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

import random
import logging

import pint
from linux_metrics import cpu_stat

from liota.dccs.rabbitmq import RabbitMQ
from liota.dcc_comms.amqp_dcc_comms import AmqpDccComms
from liota.lib.transports.amqp import AmqpPublishMessagingAttributes, AmqpConsumeMessagingAttributes
from liota.entities.metrics.metric import Metric
from liota.entities.devices.simulated_device import SimulatedDevice
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
from liota.lib.utilities.identity import Identity
from liota.lib.utilities.tls_conf import TLSConf

log = logging.getLogger(__name__)


# getting AMQP related values from conf file
config = {}
execfile('sampleProp.conf', config)

# create a pint unit registry
ureg = pint.UnitRegistry()


def custom_callback_1(body, message):
    log.info("CUSTOM CALLBACK 1 - {0}".format(str(body)))
    message.ack()


def custom_callback_2(body, message):
    log.info("CUSTOM CALLBACK 2 - {0}".format(str(body)))
    message.ack()


def custom_callback_3(body, message):
    log.info("CUSTOM CALLBACK 3 - {0}".format(str(body)))
    message.ack()


def custom_callback_4(body, message):
    log.info("CUSTOM CALLBACK 4 - {0}".format(str(body)))
    message.ack()


#  Reading CPU Utilization.
def read_cpu_utilization(sample_duration_sec=1):
    cpu_pcts = cpu_stat.cpu_percents(sample_duration_sec)
    return round((100 - cpu_pcts['idle']), 2)


#  Random number generator, simulating living room temperature readings.
def get_living_room_temperature():
    return random.randint(10, 30)


#  Random number generator, simulating living room humidity readings.
def get_living_room_humidity():
    return random.randint(70, 90)


#  Random number generator, simulating living room luminous readings.
def get_living_room_luminance():
    # 0 - Lights Off, 1 - Lights On
    return random.randint(0, 1)

# ----------------------------------------------------------------------------------------------------------------
# In this example, we demonstrate how data for a simulated metric generating
# random numbers can be directed to RabbitMQ data center component using Liota.
#
# A Simulated DHT sensor with Temperature and Humidity Metrics and a Simulated
# Digital Light sensor with binary luminance Metrics are used.
#
#
#                                            Dell5kEdgeSystem
#                                                   |
#                                                   |
#                                                   |
#                     -----------------------------------------------------
#                    |                              |                      |
#                    |                              |                      |
#                    |                              |                      |
#                 DHT Sensor                 Digital Light Sensor    CPU Utilization
#                    |                              |                   Metric
#                    |                              |
#            ----------------                  Light Metric
#           |                |
#           |                |
#      Temperature        Humidity
#         Metric           Metric
#
#
# This example showcases publishing Metrics using Mode 3 (as described in README) and without enclose_metadata.
# It also shows how to consume messages from different AMQP exchanges
# ------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    #  Creating EdgeSystem
    edge_system = Dell5KEdgeSystem(config['EdgeSystemName'])
    #  Encapsulates Identity
    identity = Identity(config['broker_root_ca_cert'], config['broker_username'], config['broker_password'],
                        cert_file=None, key_file=None)
    # Encapsulate TLS parameters
    tls_conf = TLSConf(config['cert_required'], config['tls_version'], config['cipher'])

    #  Connecting to RabbitMQ
    #  Custom Publish Topic for an EdgeSystem
    amqp_pub_msg_attr = AmqpPublishMessagingAttributes(exchange_name=config['CommonExchangeName'],
                                                       routing_key=config['CommonRoutingKey'])

    rabbitmq = RabbitMQ(AmqpDccComms(edge_system_name=edge_system.name,
                                     url=config['BrokerIP'], port=config['BrokerPort'],
                                     identity=identity, tls_conf=None,
                                     amqp_pub_msg_attr=amqp_pub_msg_attr, enable_authentication=True))

    #  Registering EdgeSystem
    reg_edge_system = rabbitmq.register(edge_system)

    #  Creating CPU Metric
    cpu_utilization = Metric(
        name="CPUUtilization",
        unit=None,
        interval=10,
        aggregation_size=2,
        sampling_function=read_cpu_utilization
    )
    #  Registering Metric and creating Parent-Child relationship
    reg_cpu_utilization = rabbitmq.register(cpu_utilization)
    rabbitmq.create_relationship(reg_edge_system, reg_cpu_utilization)
    #  Publishing Registered CPU Utilization Metric to RabbitMQ
    #  Routing-Key for this metric is config['CommonRoutingKey']
    reg_cpu_utilization.start_collecting()

    #  Creating Simulated Device
    dht_sensor = SimulatedDevice("SimulatedDHTSensor")
    #  Registering Device and creating Parent-Child relationship
    reg_dht_sensor = rabbitmq.register(dht_sensor)
    rabbitmq.create_relationship(reg_edge_system, reg_dht_sensor)
    #  Creating Temperature Metric
    temp_metric = Metric(
        name="LivingRoomTemperature",
        entity_type="Metric",
        unit=ureg.degC,
        interval=1,
        aggregation_size=5,
        sampling_function=get_living_room_temperature
    )
    #  Registering Metric and creating Parent-Child relationship
    reg_temp_metric = rabbitmq.register(temp_metric)
    rabbitmq.create_relationship(reg_dht_sensor, reg_temp_metric)
    #  Separate Exchange and Routing-Key per metric
    reg_temp_metric.msg_attr = AmqpPublishMessagingAttributes(exchange_name=config['LivingRoomTemperatureExchange'],
                                                              routing_key=config['LivingRoomTemperatureKey'])
    #  Publishing Registered Temperature Metric to RabbitMQ
    reg_temp_metric.start_collecting()

    #  Creating Humidity Metric
    hum_metric = Metric(
        name="LivingRoomHumidity",
        entity_type="Metric",
        unit=None,
        interval=1,
        aggregation_size=5,
        sampling_function=get_living_room_humidity
    )
    #  Registering Metric and creating Parent-Child relationship
    reg_hum_metric = rabbitmq.register(hum_metric)
    rabbitmq.create_relationship(reg_dht_sensor, reg_hum_metric)
    #  Separate Exchange and Routing-Key per metric
    reg_hum_metric.msg_attr = AmqpPublishMessagingAttributes(exchange_name=config['LivingRoomHumidityExchange'],
                                                             routing_key=config['LivingRoomHumidityKey'])
    #  Publishing Registered Humidity Metric to RabbitMQ
    reg_hum_metric.start_collecting()

    #  Creating Simulated Device
    light_sensor = SimulatedDevice("SimDigLightSensor")
    #  Registering Device and creating Parent-Child relationship
    reg_light_sensor = rabbitmq.register(light_sensor)
    rabbitmq.create_relationship(reg_edge_system, reg_light_sensor)

    #  Creating Light Metric
    light_metric = Metric(
        name="LivingRoomLight",
        entity_type="Metric",
        unit=None,
        interval=10,
        aggregation_size=1,
        sampling_function=get_living_room_luminance
    )
    #  Registering Metric and creating Parent-Child relationship
    reg_light_metric = rabbitmq.register(light_metric)
    rabbitmq.create_relationship(reg_light_sensor, reg_light_metric)
    #  Separate Exchange and Routing-Key per metric
    reg_light_metric.msg_attr = AmqpPublishMessagingAttributes(exchange_name=config['LivingRoomLightExchange'],
                                                               routing_key=config['LivingRoomLightKey'])
    #  Publishing Registered Light Metric to RabbitMQ
    reg_light_metric.start_collecting()
    # Consuming from different exchanges
    # For simplicity, consuming the published messages
    rabbitmq.consume([AmqpConsumeMessagingAttributes(exchange_name=config['CommonExchangeName'],
                                                     routing_keys=[config['CommonRoutingKey']],
                                                     callback=custom_callback_1
                                                     ),
                      AmqpConsumeMessagingAttributes(exchange_name=config['LivingRoomTemperatureExchange'],
                                                     routing_keys=[config['LivingRoomTemperatureKey']],
                                                     callback=custom_callback_2
                                                     ),
                      AmqpConsumeMessagingAttributes(exchange_name=config['LivingRoomHumidityExchange'],
                                                     routing_keys=[config['LivingRoomHumidityKey']],
                                                     callback=custom_callback_3
                                                     ),
                      AmqpConsumeMessagingAttributes(exchange_name=config['LivingRoomLightExchange'],
                                                     routing_keys=[config['LivingRoomLightKey']],
                                                     callback=custom_callback_4
                                                     ),

                      ])
