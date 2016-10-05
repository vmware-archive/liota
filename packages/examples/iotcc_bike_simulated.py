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

dependencies = ["iotcc", "examples/bike_simulator"]


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


class PackageClass(LiotaPackage):

    def create_udm(self, bike_model):
        ureg = bike_model.ureg

        import time
        import math

        #-------------------------------------------------------------------
        # The following functions operate on physical variables represented
        # in pint objects, and returns a pint object, too.
        # Decorators provided by the pint library are used to check the
        # dimensions of arguments passed to the functions.

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

        #-------------------------------------------------------------------
        # This is a sampling method, which queries the physical model, and
        # calls the physical functions to calculate a desired variable.

        def get_bike_speed():
            speed = get_speed(
                bike_model.get_revolution(),
                bike_model.get_radius_wheel()
            ).to(ureg.m / ureg.sec)
            return speed.magnitude

        #-------------------------------------------------------------------
        # This is a more complex sampling method, which queries the physical
        # model.

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

        self.get_bike_speed = get_bike_speed
        self.get_bike_power = get_bike_power

    def run(self, registry):
        from liota.entities.metrics.metric import Metric
        import copy

        # Acquire resources from registry
        iotcc = registry.get("iotcc")
        iotcc_edge_system = copy.copy(registry.get("iotcc_edge_system"))

        bike_simulator = registry.get("bike_simulator")

        iotcc_bike = iotcc.register(bike_simulator)
        iotcc.create_relationship(iotcc_edge_system, iotcc_bike)

        ureg = bike_simulator.ureg
        self.create_udm(bike_model=bike_simulator)

        # Create metrics
        self.metrics = []

        metric_name = "model.bike.speed"
        bike_speed = Metric(
            name=metric_name,
            unit=(ureg.m / ureg.sec),
            interval=5,
            sampling_function=self.get_bike_speed
        )
        reg_bike_speed = iotcc.register(bike_speed)
        iotcc.create_relationship(iotcc_bike, reg_bike_speed)
        reg_bike_speed.start_collecting()
        self.metrics.append(reg_bike_speed)

        metric_name = "model.bike.power"
        bike_power = Metric(
            name=metric_name,
            unit=ureg.watt,
            interval=5,
            sampling_function=self.get_bike_power
        )
        reg_bike_power = iotcc.register(bike_power)
        iotcc.create_relationship(iotcc_bike, reg_bike_power)
        reg_bike_power.start_collecting()
        self.metrics.append(reg_bike_power)

    def clean_up(self):
        for metric in self.metrics:
            metric.stop_collecting()
