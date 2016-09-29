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

import threading
import time
import random
import math
import pint
from liota.entities.devices.device import Device
from liota.lib.utilities.utility import systemUUID


class BikeSimulated(Device):

    def __init__(self, name, wheel=26, m_bike=20, m_rider=80,
                 m_load=0, interval=5, ureg=None):
        super(BikeSimulated, self).__init__(
            name=name,
            entity_id=systemUUID().get_uuid(name),
            entity_type="BikeSimulated"
        )

        self.slope = 0.0            # rad
        self.radius_wheel = wheel   # inch
        self.weight_bike = m_bike  # kg
        self.weight_rider = m_rider  # kg
        self.weight_load = m_load  # kg
        self.revolution = 0.0       # rpm
        self.area = 1.0             # m ** 2
        self.interval = interval
        self.ureg = None
        if isinstance(ureg, pint.UnitRegistry):
            self.ureg = ureg
        else:
            self.ureg = pint.UnitRegistry()
        self.time_last = None
        self.run()

    def run(self):
        self.th = threading.Thread(target=self.simulate)
        self.th.daemon = True
        self.th.start()

    #-----------------------------------------------------------------------
    # This method randomly changes some state variables in the model every a
    # few seconds (as is defined as interval).

    def simulate(self):
        while True:
            # Sleep until next cycle
            time.sleep(self.interval)

            # Change slope
            self.slope = min(
                max(self.slope +
                    random.uniform(-0.01, 0.01) * self.interval,
                    -math.pi / 16
                    ), math.pi / 16
            )

            # Change revolution
            self.revolution = min(
                max(
                    self.revolution +
                    random.uniform(-2.0, 5.0) * self.interval,
                    0
                ), 40
            )

            # Change load
            t = time.time()
            if self.time_last is None:
                self.time_last = t
            else:
                if t - self.time_last >= 30:
                    self.weight_load = random.randrange(0, 50)
                    self.time_last = t

    #-----------------------------------------------------------------------
    # These methods are used to access the state of the simulated physical
    # object. A typical caller is the sampling method for a metric in a Liota
    # application.

    def get_slope(self):
        return self.ureg.rad * self.slope

    def get_revolution(self):
        return self.ureg.rpm * self.revolution

    def get_radius_wheel(self):
        return self.ureg.inch * self.radius_wheel

    def get_weight_bike(self):
        return self.ureg.kg * self.weight_bike

    def get_weight_rider(self):
        return self.ureg.kg * self.weight_rider

    def get_weight_load(self):
        return self.ureg.kg * self.weight_load

    def get_area(self):
        return self.ureg.m ** 2 * self.area
