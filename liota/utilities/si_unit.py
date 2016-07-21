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

import re
import pint
import pint.errors
import si.units
import si.prefixes

prefixes_short = si.units.SIUnit.all_prefixes
prefixes_long = map(
        lambda pf: si.prefixes.prefix_from_value(
                getattr(si.prefixes, pf),
                short=False
            ),
        prefixes_short
    )
re_prefixes = "(" + "|".join(prefixes_long) + ")"
re_prefixed = "^" + re_prefixes + "([^\s]+)$"
cr_prefixed = re.compile(re_prefixed)
cr_replaces = {
        re.compile("meter"): "metre",
        re.compile("degC"): "degree Celsius",
        re.compile("\*\*\s2"): "squared",
        re.compile("\*\*\s3"): "cubed",
        re.compile("\*\*\s4"): "to the fourth power",
        re.compile("\s\*\s"): " ",
    }

# Find prefix with provided multiplier and return its full name
def _get_prefix(multiplier):
    return si.prefixes.prefix_from_value(multiplier, short=False)

class UnsupportedUnitError(ValueError):
    """
    Raised when the derived unit is not supported by parser
    """

    def __init__(self, unit_specs):
        super(ValueError, self).__init__()
        self.unit_specs = unit_specs

    def __str__(self):
        mess = "'{0}' is not a supported unit"
        return mess.format(self.unit_specs)

# Return name of unit according to SI specs, or return None if unit is None
def _get_unit_name(unit):
    if unit is None:
        return None

    # Get string of unit from pint
    ts = str(unit)

    if(ts == "dimensionless"):
        return None
    for cr, rp in cr_replaces.items():
        ts = cr.sub(rp, ts)

    # Detect higher powers and throw exception
    if re.compile("\d").search(ts) is not None:
    	raise UnsupportedUnitError(unit)

    # Additional and advanced replacements
    ts = re.compile("\s\/\s").sub(" per ", ts, count=1)
    ts = re.compile("\s\/\s").sub(" ", ts, count=1)

    return ts

def parse_unit(unit):
    pf = None
    un = None
    if unit is None:
        return (pf, _get_unit_name(un))
    ureg = unit._REGISTRY

    # We require developers to use MKS base units
    assert ureg.default_system == "mks"

    # Attempt to extract prefix using string matching
    re_match = cr_prefixed.search(str(unit))
    if re_match is not None:
        ut = getattr(ureg, re_match.group(2))
        tn = ureg.get_base_units(ut)
        if tn[0] == 1:
            pf = re_match.group(1)
            un = ut
            return (pf, _get_unit_name(un))

    # Attempt to extract prefix using base unit conversion
    tn = ureg.get_base_units(unit)
    if tn[0] == 1: # Base unit, or simple combination of several base units
        if tn[1] != ureg.dimensionless:
            un = unit
    else: # Prefixed unit, or non-SI unit
        try:
            pf = _get_prefix(tn[0])
            un = tn[1]
            if re.compile("\s").search(str(un)) is not None:
            	raise UnsupportedUnitError(unit)
        except IndexError:
            raise UnsupportedUnitError(unit)

    # Return prefix and unit strings
    return (pf, _get_unit_name(un))

# Testing code
def main():
    ureg = pint.UnitRegistry()

    pint_units = []
    pint_units.append(ureg.m / ureg.m)
    pint_units.append(ureg.rad)
    pint_units.append(ureg.deg)
    pint_units.append(ureg.um)
    pint_units.append(ureg.feet)
    pint_units.append(ureg.mg)
    pint_units.append(ureg.degC)
    pint_units.append(ureg.degF)
    pint_units.append(ureg.acre)
    pint_units.append(ureg.m ** 2)
    pint_units.append(ureg.L)
    pint_units.append(ureg.m / ureg.s)
    pint_units.append(ureg.m / ureg.s ** 2)
    pint_units.append(ureg.newton)
    pint_units.append(ureg.kg * ureg.m / ureg.s ** 2)
    pint_units.append(ureg.J / ureg.kg / ureg.K)
    pint_units.append(ureg.pascal)
    pint_units.append(ureg.kV)
    pint_units.append(ureg.megaohm)
    pint_units.append(ureg.uF)

    print_split = "-" * 76

    print print_split
    print "\033[1m%32s    %s\033[0m" % (
            "String (Pint)",
            "Name and Prefix"
        )
    print print_split
    for un in pint_units:
        pf = "\033[1;36mnull\033[0m"
        qn = None
        try:
            qn = parse_unit(un)
        except UnsupportedUnitError as ex:
            # print ex
            pf = "\033[1;31minvalid\033[0m" 
        if qn is not None:
            if qn[0] is not None:
                pf = "\033[1;33m" + qn[0] + "\033[0m"
        nn = "\033[1;31minvalid\033[0m"
        if qn is not None:
            if qn[1] is not None:
                nn = qn[1]
            else:
                nn = "\033[1;36mnull\033[0m"
        print "\033[1m%32s\033[0m    %s, %s" % (un, nn, pf)
    print print_split
    # print "All supported prefixes: {0}".format(prefixes_long)

if __name__ == "__main__":
    main()
