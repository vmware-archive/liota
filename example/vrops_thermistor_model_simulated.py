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

from thermistor_model_simulated import ThermistorModelSimulated

# create a pint unit registry
ureg = pint.UnitRegistry()

# initialize and run the physical model (simulated device)
thermistor_model = ThermistorModelSimulated(ureg=ureg)
thermistor_model.run()

#---------------------------------------------------------------------------
# The following functions operate on physical variables represented in
# pint objects, and returns a pint object, too.
# Decorators provided by the pint library are used to check the dimensions of
# arguments passed to the functions.

@ureg.check(ureg.volt, ureg.ohm, ureg.volt)
def get_rx(u, r0, ux):
    rx = r0 * ux / (u - ux)
    return rx

@ureg.check(1 / ureg.kelvin, 1 / ureg.kelvin, 1 / ureg.kelvin, ureg.ohm)
def get_temperature(c1, c2, c3, rx):
    temper = 1 / ( \
            c1 + \
            c2 * math.log(rx / ureg.ohm) + \
            c3 * math.log(rx / ureg.ohm) ** 3
        )
    return temper

#---------------------------------------------------------------------------
# This is a sampling method, which queries the physical model, and calls the
# physical functions to calculate a desired variable.
# In this specific case, it gets the coefficients, voltages, and reference
# resistance from the thermistor simulator, and calls the methods defined
# above to get the temperature.

def get_thermistor_temperature():
    temper = get_temperature(
            thermistor_model.get_c1(),
            thermistor_model.get_c2(),
            thermistor_model.get_c3(),
            get_rx(
                    thermistor_model.get_u(),
                    thermistor_model.get_r0(),
                    thermistor_model.get_ux()
                )
        ).to(ureg.degC)
    return temper.magnitude

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
    thermistor = Function("Thermistor Model", 'Read', gateway)
    vrops_thermistor = vrops.register(thermistor)
    if vrops_thermistor.registered:
        for item in config['Device1PropList']:
            for key, value in item.items():
                vrops.set_properties(key, value, vrops_thermistor)
        thermistor_temper = vrops.create_metric(vrops_thermistor, "Temperature",
                unit=None, sampling_interval_sec=5,
                sampling_function=get_thermistor_temperature)
        thermistor_temper.start_collecting()
    else:
        print "vROPS resource not registered successfully"

