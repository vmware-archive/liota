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
from liota.lib.utilities.utility import read_user_config

dependencies = ["iotcc", "examples/thermistor_simulator"]


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


class PackageClass(LiotaPackage):

    def create_udm(self, thermistor_model):
        ureg = thermistor_model.ureg

        import math

        #-------------------------------------------------------------------
        # The following functions operate on physical variables represented
        # in pint objects, and returns a pint object, too.
        # Decorators provided by the pint library are used to check the
        # dimensions of arguments passed to the functions.

        @ureg.check(ureg.volt, ureg.ohm, ureg.volt)
        def get_rx(u, r0, ux):
            rx = r0 * ux / (u - ux)
            return rx

        @ureg.check(
            1 / ureg.kelvin,
            1 / ureg.kelvin,
            1 / ureg.kelvin,
            ureg.ohm)
        def get_temperature(c1, c2, c3, rx):
            temper = 1 / (
                c1 +
                c2 * math.log(rx / ureg.ohm) +
                c3 * math.log(rx / ureg.ohm) ** 3
            )

            #---------------------------------------------------------------
            # Here commented is a counter example, showing how a dimension
            # mismatch can be prevented using pint.
            # Since in the correct one above, the unit of temper is
            # already Kelvin, if we multiply it by ureg.kelvin, the unit of
            # the returned values will become ureg.kelvin ** 2, which will
            # consequently throw an exception in succeeding method calls.

            # temper = 1 / ( \
            #         c1 + \
            #         c2 * math.log(rx / ureg.ohm) + \
            #         c3 * math.log(rx / ureg.ohm) ** 3
            #     ) * ureg.kelvin

            return temper

        #-------------------------------------------------------------------
        # This is a sampling method, which queries the physical model, and
        # calls the physical functions to calculate a desired variable.
        # In this specific case, it gets the coefficients, voltages, and
        # reference resistance from the thermistor simulator, and calls the
        # methods defined above to get the temperature.

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

        self.get_thermistor_temperature = get_thermistor_temperature

    def run(self, registry):
        from liota.entities.metrics.metric import Metric
        import copy

        # Acquire resources from registry
        self.config_path = registry.get("package_conf")
        self.iotcc = registry.get("iotcc")
        self.iotcc_edge_system = copy.copy(registry.get("iotcc_edge_system"))
        thermistor_simulator = registry.get("thermistor_simulator")
        
        self.iotcc_thermistor = self.iotcc.register(thermistor_simulator)
        self.iotcc.create_relationship(self.iotcc_edge_system, self.iotcc_thermistor)

        ureg = thermistor_simulator.ureg
        self.create_udm(thermistor_model=thermistor_simulator)

        # Create metrics
        self.metrics = []
        metric_name = "model.thermistor.temperature"
        thermistor_temper = Metric(
            name=metric_name,
            unit=ureg.degC,
            interval=5,
            sampling_function=self.get_thermistor_temperature
        )
        reg_thermistor_temper = self.iotcc.register(thermistor_temper)
        self.iotcc.create_relationship(self.iotcc_thermistor, reg_thermistor_temper)
        reg_thermistor_temper.start_collecting()
        self.metrics.append(reg_thermistor_temper)

        # Use the iotcc_device_name as identifier in the registry to easily refer the registered device in other packages
        registry.register("iotcc_thermistor_simulated", self.iotcc_thermistor)

    def clean_up(self):

        # Get values from configuration file
        config = read_user_config(self.config_path + '/sampleProp.conf')

        for metric in self.metrics:
            metric.stop_collecting()

        #Unregister iotcc device
        if config['ShouldUnregisterOnUnload'] == "True":
            self.iotcc.unregister(self.iotcc_thermistor)
