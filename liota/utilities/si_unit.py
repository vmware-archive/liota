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

#---------------------------------------------------------------------------
# SI prefixes, according to standard documents
# http://www.bipm.org/en/measurement-units/

prefixes = {
        10.0:       "deca",     0.1:        "deci",
        100.0:      "hecto",    0.01:       "centi",
        1000.0:     "kilo",     0.001:      "milli",
        1e+6:       "mega",     1e-6:       "micro",
        1e+9:       "giga",     1e-9:       "nano",
        1e+12:      "tera",     1e-12:      "pico",
        1e+15:      "peta",     1e-15:      "femto",
        1e+18:      "exa",      1e-18:      "atto",
        1e+21:      "zetta",    1e-21:      "zepto",
        1e+24:      "yotta",    1e-24:      "yocto"
    }
prefixes_long = prefixes.values()

#---------------------------------------------------------------------------
# These are regular expression objects we use to convert pint strings to
# standard SI unit names.
# May need to be changed if pint strings are changed in a pint update

re_prefixes = "(" + "|".join(prefixes_long) + ")"
re_prefixed = "^" + re_prefixes + "([^\s]+)$"
cr_prefixed = re.compile(re_prefixed)

# Compiled regular expression objects for batch replacements
cr_replaces = {
        re.compile(r"\bmeter\b"): "metre",
        re.compile(r"\bdegC\b"): "degree Celsius",
        re.compile(r"Bq\b"): "becquerel",
        re.compile(r"Gy\b"): "gray",
        re.compile(r"\*\*\s2\b"): "squared",
        re.compile(r"\*\*\s3\b"): "cubed",
        re.compile(r"\*\*\s4\b"): "to the fourth power",
        re.compile(r"\b1\s\/\s(meter|metre)"): r"reciprocal \1",
        re.compile(r"\s\*\s"): " "
    }
cr_patches = {
		re.compile(r"metre\ssquared"): "square metre",
		re.compile(r"metre\scubed"): "cubic metre",
		re.compile(r"(kelvin|degree\sCelsius)\skilogram"): r"kilogram \1",
		re.compile(r"(kelvin|degree\sCelsius)\smetre"): r"metre \1",
		re.compile(r"(kelvin|degree\sCelsius)\smole"): r"mole \1",
		re.compile(r"metre\snewton"): "newton metre"
	}

# Find prefix with provided multiplier and return its full name
def _get_prefix(multiplier):
    return prefixes[multiplier]

#---------------------------------------------------------------------------
# Here we defined an error that is raised when we cannot parse user defined
# unit for whatever reason.
# Currently, possible reasons include using non-SI unit, having prefix on a
# squared or cubed unit, and having unsupported power of unit.

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

#---------------------------------------------------------------------------
# This method returns name of unit according to SI specs,
# or return None if provided unit reference is None.

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
    if re.compile("\*\*\s\-?\d").search(ts) is not None:
        raise UnsupportedUnitError(unit)

    # Detect numbers and throw exception
    if re.compile("\d").search(ts) is not None:
        raise UnsupportedUnitError(unit)    

    # Additional and advanced replacements
    ts = re.compile(r"\s\/\s").sub(" per ", ts, count=1)
    ts = re.compile(r"\s\/\s").sub(" ", ts, count=1)

    # Apply name patches
    for cr, rp in cr_patches.items():
        ts = cr.sub(rp, ts)

    return ts

#---------------------------------------------------------------------------
# This is primary method that should be imported in vROps DCC, or any future
# DCC that has or requires unit support, in order to parse unit parameter
# passed through create_metric call.

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
            # if re.compile("\s").search(str(un)) is not None:
            if re.compile("\d").search(str(un)) is not None:
                raise UnsupportedUnitError(unit)
        except KeyError:
            raise UnsupportedUnitError(unit)

    # Return prefix and unit strings
    return (pf, _get_unit_name(un))

#---------------------------------------------------------------------------
# These are units defined in tables from standard documents.
# Table 1 include seven base units.
# Table 2-4 include examples of derived units.
# We want to make sure all units defined in these tables are parsed as they 
# are specified in standard documents.
# For derived units not in these tables, we deliver out best effort.

units_table_1 = lambda ureg: [
        ureg.m,     ureg.kg,    ureg.s,     ureg.A,     ureg.K,
        ureg.mol,   ureg.cd
    ]
units_table_2 = lambda ureg: [
        ureg.m ** 2,            ureg.m ** 3,
        ureg.m / ureg.s,        ureg.m / ureg.s ** 2,
        ureg.m ** -1,
        ureg.kg / ureg.m ** 3,  ureg.kg / ureg.m ** 2,
        ureg.m ** 3 / ureg.kg,
        ureg.A / ureg.m ** 2,   ureg.A / ureg.m,
        ureg.mol / ureg.m ** 3, ureg.kg / ureg.m ** 3,
        ureg.cd / ureg.m ** 2,
        ureg.dimensionless,     ureg.dimensionless
    ]
units_table_3 = lambda ureg: [
        ureg.rad,   ureg.sr,    ureg.Hz,    ureg.N,     ureg.Pa,
        ureg.J,     ureg.W,     ureg.C,     ureg.V,     ureg.F,
        ureg.ohm,   ureg.S,     ureg.Wb,    ureg.T,     ureg.H,
        ureg.degC,  ureg.lm,    ureg.lx,    ureg.Bq,    ureg.Gy,
        ureg.Sv,
        ureg.mol / ureg.s # katal (kat) is not supported by pint at this time
    ]
units_table_4 = lambda ureg: [
        ureg.Pa * ureg.s,
        ureg.N * ureg.m,        ureg.N / ureg.m,
        ureg.rad / ureg.s,      ureg.rad / ureg.s ** 2,
        ureg.W / ureg.m ** 2,
        ureg.J / ureg.K,        ureg.J / (ureg.kg * ureg.K),
        ureg.J / ureg.kg,       ureg.W / (ureg.m * ureg.K),
        ureg.J / ureg.m ** 3,
        ureg.V / ureg.m,        ureg.C / ureg.m ** 3,
        ureg.C / ureg.m ** 2,   ureg.C / ureg.m ** 2,
        ureg.F / ureg.m,        ureg.H / ureg.m,
        ureg.J / ureg.mol,      ureg.J / (ureg.mol * ureg.K),
        ureg.C / ureg.kg,       ureg.Gy / ureg.s,
        ureg.W / ureg.sr,       ureg.W / (ureg.m ** 2 * ureg.sr),
        (ureg.mol / ureg.s) / ureg.m ** 3
    ]
unit_tables = lambda ureg: [
        units_table_1(ureg),
        units_table_2(ureg),
        units_table_3(ureg),
        units_table_4(ureg)
    ]


# Testing code
def main():
    ureg = pint.UnitRegistry()
    print_split = "-" * 76

    # Base units and examples of derived units defined in SI standard documents
    def parse_unit_with_color(un):
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
        return (pf, nn)

    for j in range(0, 4):
        print print_split
        print "  \033[1;36mTable %d\033[0m" % (j + 1)
        print print_split
        for un in unit_tables(ureg)[j]:
            pf, nn = parse_unit_with_color(un)
            print "  \033[1m%s\033[0m - %s, %s" % (un, pf, nn)
    
    print print_split
    print "  \033[1;33mSupported Prefixes\033[0m"
    print print_split
    for multiplier, pf in sorted(prefixes.items()):
        print "  \033[1m%s\033[0m = %.2e" % (pf, multiplier)

    units_prefixed = [
            ureg.km,    ureg.dm,    ureg.cm,    ureg.mm,    ureg.um,
            ureg.nm,    ureg.fm,    ureg.pm,
            ureg.kg,    ureg.g,     ureg.mg,    ureg.ug,
            ureg.ms,    ureg.us,    ureg.ns,    ureg.fs,
            ureg.mA,    ureg.uA,    ureg.mmol,
            ureg.GHz,   ureg.MHz,   ureg.kHz,
            ureg.MPa,   ureg.kPa,   ureg.hPa,
            ureg.kJ,    ureg.MW,    ureg.kW,    ureg.mW,
            ureg.MV,    ureg.kV,    ureg.mV,
            ureg.uF,    ureg.nF,    ureg.pF,
            ureg.Mohm,  ureg.kohm,
        ]

    print print_split
    print "  \033[1;33mPrefixed Units\033[0m"
    print print_split
    for un in units_prefixed:
        pf, nn = parse_unit_with_color(un)
        print "  \033[1m%s\033[0m - %s, %s" % (un, pf, nn)

    units_invalid = [
            ureg.deg,   ureg.ft,    ureg.inch,  ureg.yard,  ureg.mile,
            ureg.degF,
            ureg.acre,
            ureg.km ** 2,           ureg.dm ** 2,
            ureg.L,
            ureg.dm ** 3,           ureg.cm ** 2,
            ureg.kph,
            ureg.km / ureg.s,
            ureg.um / ureg.ms,
            ureg.kWh,
            ureg.s ** -1,           ureg.kg ** -1
        ]

    print print_split
    print "  \033[1;31mInvalid Units\033[0m"
    print print_split
    for un in units_invalid:
        pf, nn = parse_unit_with_color(un)
        print "  \033[1m%s\033[0m - %s, %s" % (un, pf, nn)

    print print_split

if __name__ == "__main__":
    main()
