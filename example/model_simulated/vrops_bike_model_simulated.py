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

from liota.boards.gateway_dk300 import Dk300
from liota.dcc.vrops import Vrops
from liota.things.function import Function
from liota.transports.web_socket import WebSocket
import random

# getting values from conf file
config = {}
execfile('sampleProp.conf', config)

import time
import math
import pint

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

from bike_model_simulated import BikeModelSimulated

# create a pint unit registry
ureg = pint.UnitRegistry()

# initialize and run the physical model (simulated device)
bike_model = BikeModelSimulated(ureg=ureg)
bike_model.run()

#---------------------------------------------------------------------------
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

#---------------------------------------------------------------------------
# This is a sampling method, which queries the physical model, and calls the
# physical functions to calculate a desired variable.

def get_bike_speed():
    speed = get_speed(
            bike_model.get_revolution(),
            bike_model.get_radius_wheel()
        ).to(ureg.m / ureg.sec)
    return speed.magnitude

#---------------------------------------------------------------------------
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

#---------------------------------------------------------------------------
# In this example, we demonstrate how simulated data can be directed to vROps,
# VMware's data center component using Liota.

if __name__ == '__main__':

    # create a data center object, vROps in this case, using websocket as a transport layer
    # this object encapsulates the formats and protocols neccessary for the agent to interact with the dcc
    # UID/PASS login for now.
    vrops = Vrops(config['vROpsUID'], config['vROpsPass'], WebSocket(url=config['WebSocketUrl']))

    # create a gateway object encapsulating the particulars of a gateway/board
    # argument is the name of this gateway
    gateway = Dk300(config['Gateway1Name'])

    # resister the gateway with the vrops instance
    # this call creates a representation (a Resource) in vrops for this gateway with the name given
    vrops_gateway = vrops.register(gateway)

    if vrops_gateway.registered:
        # these call set properties on the Resource representing the gateway in the vrops instance
        # properties are a key:value store
        # arguments are (key, value)
        for item in config['Gateway1PropList']:
            for key, value in item.items():
                vrops.set_properties(key, value, vrops_gateway)
    else:
        print "vROPS resource not registered successfully"

    # create the device object and register it on vROps
    bike = Function("Bike Model", 'Read', gateway)
    vrops_bike = vrops.register(bike)
    if vrops_bike.registered:
        for item in config['Device1PropList']:
            for key, value in item.items():
                vrops.set_properties(key, value, vrops_bike)
        bike_speed = vrops.create_metric(vrops_bike, "Speed",
                unit=(ureg.m / ureg.sec), sampling_interval_sec=5,
                sampling_function=get_bike_speed)
        bike_speed.start_collecting()
        bike_speed = vrops.create_metric(vrops_bike, "Power",
                unit=ureg.watt, sampling_interval_sec=5,
                sampling_function=get_bike_power)
        bike_speed.start_collecting()
    else:
        print "vROPS resource not registered successfully"

