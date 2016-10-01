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

import math
import pint
from liota.dcc_comms.socket_comms import Socket
from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem
from liota.entities.devices.thermistor_simulated import ThermistorSimulated

# getting values from conf file
config = {}
execfile('../sampleProp.conf', config)

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

# create a pint unit registry
ureg = pint.UnitRegistry()

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
    temper = 1 / (
        c1 +
        c2 * math.log(rx / ureg.ohm) +
        c3 * math.log(rx / ureg.ohm) ** 3
    )

    #-----------------------------------------------------------------------
    # Here commented is a counter example, showing how a dimension mismatch
    # can be prevented using pint.
    # Since in the correct one above, the unit of temper is
    # already Kelvin, if we multiply it by ureg.kelvin, the unit of the
    # returned values will become ureg.kelvin ** 2, which will consequently
    # throw an exception in succeeding method calls.

    # temper = 1 / ( \
    #         c1 + \
    #         c2 * math.log(rx / ureg.ohm) + \
    #         c3 * math.log(rx / ureg.ohm) ** 3
    #     ) * ureg.kelvin

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
    return temper.magnitude  # return a scalar for compatibility

#---------------------------------------------------------------------------
# In this example, we demonstrate how data from a simulated device generating
# random physical variables can be directed to graphite data center component
# using Liota.

if __name__ == '__main__':

    edge_system = Dell5KEdgeSystem(config['EdgeSystemName'])

    # initialize and run the physical model (simulated device)
    thermistor_model = ThermistorSimulated(name=config['DeviceName'], ureg=ureg)

    # Sending data to a data center component
    # Graphite is a data center component
    # Socket is the transport which the agent uses to connect to the graphite
    # instance
    graphite = Graphite(Socket(ip=config['GraphiteIP'],
                               port=config['GraphitePort']))

    graphite_reg_dev = graphite.register(thermistor_model)

    metric_name = "model.thermistor.temperature"
    thermistor_temper = Metric(
        name=metric_name,
        unit=ureg.degC,
        interval=5,
        sampling_function=get_thermistor_temperature
    )
    reg_thermistor_temper = graphite.register(thermistor_temper)
    graphite.create_relationship(graphite_reg_dev, reg_thermistor_temper)
    reg_thermistor_temper.start_collecting()
