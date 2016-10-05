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
import pint
from liota.entities.devices.device import Device
from liota.lib.utilities.utility import systemUUID


class ThermistorSimulated(Device):

    def __init__(self, name, u=5.0, r0=3000, interval=5, ureg=None):
        super(ThermistorSimulated, self).__init__(
            name=name,
            entity_id=systemUUID().get_uuid(name),
            entity_type="ThermistorSimulated"
        )

        self.u = u                  # Total voltage
        self.r0 = r0                # Reference resistor
        self.ux = self.u / 2        # Initial voltage on thermistor
        self.c1 = 1.40e-3
        self.c2 = 2.37e-4
        self.c3 = 9.90e-8
        self.interval = interval
        self.ureg = None
        if isinstance(ureg, pint.UnitRegistry):
            self.ureg = ureg
        else:
            self.ureg = pint.UnitRegistry()

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

            self.ux = min(
                max(
                    self.ux +
                    random.uniform(-0.01, 0.01) * self.interval,
                    1.5
                ), 3.5
            )

    #-----------------------------------------------------------------------
    # These methods are used to access the state of the simulated physical
    # object. A typical caller is the sampling method for a metric in a Liota
    # application.

    def get_u(self):
        return self.ureg.volt * self.u

    def get_r0(self):
        return self.ureg.ohm * self.r0

    def get_ux(self):
        return self.ureg.volt * self.ux

    def get_c1(self):
        return self.c1 / self.ureg.kelvin

    def get_c2(self):
        return self.c2 / self.ureg.kelvin

    def get_c3(self):
        return self.c3 / self.ureg.kelvin
