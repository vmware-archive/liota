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

from pint import UnitRegistry
from temperusb import TemperHandler
from liota.dcc_comms.socket_comms import SocketDccComms
from liota.dccs.graphite import Graphite
from liota.entities.metrics.metric import Metric
from liota.entities.edge_systems.dk300_edge_system import Dk300EdgeSystem
from liota.lib.utilities.utility import read_user_config

# getting values from conf file
config = read_user_config('sampleProp.conf')
ureg = UnitRegistry()
quantity = ureg.Quantity

# ---------------------------------------------------------------------------
# Below we showcase how easily SI units can be used in the code with help of
# Pint library which is part of Liota and how easily conversion of the units
# can be done such as Celsius to Fahrenheit or Kelvin as shown below with
# help of this library.

def getTemp():
    th = TemperHandler()
    devs = th.get_devices()
    t = devs[0].get_temperatures()
    temp = quantity(t[0]['temperature_c'], ureg.degC)
    return temp


def getTempDegC():
    temp_degC = getTemp()
    return temp_degC.magnitude


def getTempDegF():
    temp = getTemp()
    temp_degF = temp.to('degF')
    return temp_degF.magnitude


def getTempKelvin():
    temp = getTemp()
    temp_kelvin = temp.to('kelvin')
    return temp_kelvin.magnitude

# --------------------------------------------------------------------------
# In this example, we demonstrate how data from a simulated device generating
# random numbers can be directed to graphite data center component using Liota.
# The program illustrates the ease of use Liota brings to IoT application developers.

if __name__ == '__main__':

    edge_system = Dk300EdgeSystem(config['EdgeSystemName'])

    # Sending data to Graphite data center component
    # Socket is the underlying transport used to connect to the Graphite
    # instance
    graphite = Graphite(SocketDccComms(ip=config['GraphiteIP'],
                               port=config['GraphitePort']))
    graphite_reg_edge_system = graphite.register(edge_system)

    metric_name_temp_degC = config['MetricNameTempDegC']
    temp_metric_degC = Metric(
        name=metric_name_temp_degC,
        unit=ureg.degC,
        interval=33,
        aggregation_size=6,
        sampling_function=getTempDegC
    )
    reg_temp_metric_degC = graphite.register(temp_metric_degC)
    graphite.create_relationship(graphite_reg_edge_system, reg_temp_metric_degC)
    reg_temp_metric_degC.start_collecting()

    metric_name_temp_degF = config['MetricNameTempDegF']
    temp_metric_degF = Metric(
        name=metric_name_temp_degF,
        unit=ureg.degF,
        interval=62,
        aggregation_size=1,
        sampling_function=getTempDegF
    )
    reg_temp_metric_degF = graphite.register(temp_metric_degF)
    graphite.create_relationship(graphite_reg_edge_system, reg_temp_metric_degF)
    reg_temp_metric_degF.start_collecting()

    metric_name_temp_kelvin = config['MetricNameTempKelvin']
    temp_metric_kelvin = Metric(
        name=metric_name_temp_kelvin,
        unit=ureg.kelvin,
        interval=0,
        aggregation_size=1,
        sampling_function=getTempKelvin
    )
    reg_temp_metric_kelvin = graphite.register(temp_metric_kelvin)
    graphite.create_relationship(graphite_reg_edge_system, reg_temp_metric_kelvin)
    reg_temp_metric_kelvin.start_collecting()
