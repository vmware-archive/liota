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

from liota.entities.edge_systems.dk300_edge_system import Dk300EdgeSystem
from liota.lib.utilities.identity import Identity
from liota.dccs.iotcc import IotControlCenter
from liota.entities.metrics.metric import Metric
from liota.entities.devices.bike_simulated import BikeSimulated
from liota.dcc_comms.websocket_dcc_comms import WebSocketDccComms
from liota.dccs.dcc import RegistrationFailure
from liota.lib.utilities.utility import read_user_config


# getting values from conf file
config = read_user_config('../sampleProp.conf')

import time
import math
import pint


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate

# create a pint unit registry
ureg = pint.UnitRegistry()

# ---------------------------------------------------------------------------
# The following functions operate on physical variables represented in
# pint objects, and returns a pint object, too.
# Decorators provided by the pint library are used to check the dimensions of
# arguments passed to the functions.

@ureg.check(ureg.rpm, ureg.m)
def get_speed(revolution, radius):
    return revolution * radius


@ureg.check(ureg.m / ureg.sec)
@static_vars(speed_last=None, time_last=None)
def get_acceleration(speed):
    t = time.time()
    if get_acceleration.time_last is None:
        acc = 0 * ureg.m / ureg.sec ** 2
    else:
        acc = (speed - get_acceleration.speed_last) / \
              ((t - get_acceleration.time_last) * ureg.sec)
    get_acceleration.speed_last = speed
    get_acceleration.time_last = t
    return acc


@ureg.check(ureg.m ** 2, ureg.m / ureg.sec, ureg.kg / ureg.m ** 3)
def get_resistance(area, speed, k):
    return (k * area * speed ** 2)


@ureg.check(ureg.kg, ureg.m / ureg.sec ** 2)
def get_force(mass, acceleration):
    return mass * acceleration


@ureg.check(ureg.newton, ureg.m / ureg.sec)
def get_power(force, speed):
    return force * speed


# ---------------------------------------------------------------------------
# This is a sampling method, which queries the physical model, and calls the
# physical functions to calculate a desired variable.

def get_bike_speed():
    speed = get_speed(
        bike_model.get_revolution(),
        bike_model.get_radius_wheel()
    ).to(ureg.m / ureg.sec)
    return speed.magnitude


# ---------------------------------------------------------------------------
# This is a more complex sampling method, which queries the physical model.

def get_bike_power():
    weight_total = bike_model.get_weight_bike() + \
                   bike_model.get_weight_rider() + \
                   bike_model.get_weight_load()
    speed = get_speed(
        bike_model.get_revolution(),
        bike_model.get_radius_wheel()
    )
    power_acceleration = get_power(
        get_force(
            weight_total,
            get_acceleration(speed)
        ),
        speed
    ).to(ureg.watt)
    power_gravity = get_power(
        get_force(
            weight_total,
            9.8 * ureg.m / ureg.sec ** 2
        ),
        speed * math.sin(bike_model.get_slope())
    ).to(ureg.watt)
    power_resistance = get_power(
        get_resistance(
            bike_model.get_area(),
            speed,
            10 * ureg.kg / ureg.m ** 3
        ).to(ureg.newton),
        speed
    ).to(ureg.watt)
    power = power_acceleration + power_gravity + power_resistance
    return power.to(ureg.watt).magnitude


# ---------------------------------------------------------------------------
# In this example, we demonstrate how simulated data can be directed to IoTCC
# VMware's data center component using Liota.

if __name__ == '__main__':

    # create a data center object, IotCC in this case, using websocket as a transport layer
    # this object encapsulates the formats and protocols neccessary for the agent to interact with the dcc
    # UID/PASS login for now.
    identity = Identity(root_ca_cert=config['WebsocketCaCertFile'], username=config['IotCCUID'],
                        password=config['IotCCPassword'],
                        cert_file=config['ClientCertFile'], key_file=config['ClientKeyFile'])

    # Initialize DCC object with transport
    iotcc = IotControlCenter(
        WebSocketDccComms(url=config['WebSocketUrl'], verify_cert=config['VerifyServerCert'], identity=identity)
    )

    try:

        # create a Edge System object encapsulating the particulars of a gateway/board
        # argument is the name of this Edge System
        edge_system = Dk300EdgeSystem(config['EdgeSystemName'])

        # resister the Edge System with the IoTCC instance
        # this call creates a representation (a Resource) in IoTCC for this IoT System with the name given
        reg_edge_system = iotcc.register(edge_system)

        # these call set properties on the Resource representing the IoT System
        # properties are a key:value store
        reg_edge_system.set_properties(config['SystemPropList'])

        # create the device object and register it on IoTCC
        bike_model = BikeSimulated(name=config['DeviceName'], ureg=ureg)

        reg_bike_model = iotcc.register(bike_model)
        iotcc.create_relationship(reg_edge_system, reg_bike_model)

        reg_bike_model.set_properties(config['DevicePropList'])

        # Publish bike speed metrics to IoTCC
        metric_name_bike_speed = "model.bike.speed"
        bike_speed = Metric(
            name=metric_name_bike_speed,
            unit=(ureg.m / ureg.sec),
            interval=5,
            sampling_function=get_bike_speed
        )
        reg_bike_speed = iotcc.register(bike_speed)
        iotcc.create_relationship(reg_bike_model, reg_bike_speed)
        reg_bike_speed.start_collecting()

        # Publish bike power metrics to IoTCC
        metric_name_bike_power = "model.bike.power"
        bike_power = Metric(
            name=metric_name_bike_power,
            unit=ureg.watt,
            interval=5,
            sampling_function=get_bike_power
        )

        reg_bike_power = iotcc.register(bike_power)
        iotcc.create_relationship(reg_bike_model, reg_bike_power)
        reg_bike_power.start_collecting()

    except RegistrationFailure:
        print "Registration to IOTCC failed"
