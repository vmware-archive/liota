# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2017 VMware, Inc. All Rights Reserved.                    #
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
import unittest

from liota.lib.utilities.si_unit import *


class TestSIUnits(unittest.TestCase):
    ureg = pint.UnitRegistry()

    # able to parse, just doesn't have a prefix
    units_not_prefixed = [
        ureg.kg,
    ]

    # all around usable units
    units_prefixed = [
        ureg.km, ureg.dm, ureg.cm, ureg.mm, ureg.um,
        ureg.nm, ureg.fm, ureg.pm,
        ureg.g, ureg.mg, ureg.ug,
        ureg.ms, ureg.us, ureg.ns, ureg.fs,
        ureg.mA, ureg.uA, ureg.mmol,
        ureg.GHz, ureg.MHz, ureg.kHz,
        ureg.MPa, ureg.kPa, ureg.hPa,
        ureg.kJ, ureg.MW, ureg.kW, ureg.mW,
        ureg.MV, ureg.kV, ureg.mV,
        ureg.uF, ureg.nF, ureg.pF,
        ureg.Mohm, ureg.kohm,
        ureg.km / ureg.s,
        ureg.um / ureg.ms,
    ]

    # units that aren't supported in liota
    units_unsupported = [
        ureg.deg, ureg.ft, ureg.inch, ureg.yard, ureg.mile,
        ureg.degF,
        ureg.acre,
        ureg.km ** 2, ureg.dm ** 2,
        ureg.L,
        ureg.dm ** 3, ureg.cm ** 2,
        ureg.kph,
        ureg.kWh,
        ureg.s ** -1, ureg.kg ** -1
    ]

    # units that are invalid to pint
    units_invalid = [
        None
    ]

    def test_valid_prefixes_si_units(self):
        for obj_unit in TestSIUnits.units_prefixed:
            str_prefix, str_unit_name = parse_unit(obj_unit)
            assert str_prefix is not None and str_prefix != "invalid", repr(obj_unit) + " unit didn't have prefix"

    def test_no_valid_prefixes_si_units(self):
        for obj_unit in TestSIUnits.units_not_prefixed:
            str_prefix, str_unit_name = parse_unit(obj_unit)
            assert str_prefix is None or \
                str_prefix == "invalid", \
                repr(obj_unit) + " unit wasn't supposed to have prefix"

    def test_invalid_si_units(self):
        for obj_unit in TestSIUnits.units_invalid:
            str_prefix, str_unit_name = parse_unit(obj_unit)
            assert str_prefix is None or str_prefix == "invalid", repr(
                obj_unit) + " unit prefix was supposed to be invalid"
            assert str_unit_name is None or str_unit_name == "invalid", repr(
                obj_unit) + " unit was supposed to be invalid"

    def test_unsupported_si_units(self):
        for obj_unit in TestSIUnits.units_unsupported:
            with self.assertRaises(UnsupportedUnitError):
                parse_unit(obj_unit)

if __name__ == '__main__':
    unittest.main()
