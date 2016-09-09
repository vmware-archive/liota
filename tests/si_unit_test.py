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

from liota.lib.utilities.si_unit import *

#---------------------------------------------------------------------------
# This is a testing script of module liota.utilities.si_unit
# Purpose of this script is to show parsing results of units from SI example
# tables in their documents are same with their standard names listed in
# documents.
# This script also added some examples of prefixed units and invalid unit.
# Invalid units are those we couldn't handle for now. DO NOT use them in
# user applications.
#
def main():
    ureg = pint.UnitRegistry()
    print_split = "-" * 76

    # Color strings for terminal
    c_bold = lambda str:  "\033[1m" + str + "\033[0m"
    c_red = lambda str:  "\033[31m" + str + "\033[0m"
    c_yellow = lambda str:  "\033[33m" + str + "\033[0m"
    c_cyan = lambda str:  "\033[36m" + str + "\033[0m"

    # Base units and examples of derived units defined in SI standard documents
    def parse_unit_with_color(obj_unit):
        str_prefix = c_bold(c_cyan("null"))
        tuple_parsed_unit = None
        try:
            tuple_parsed_unit = parse_unit(obj_unit)
        except UnsupportedUnitError as ex:
            # print ex
            str_prefix = c_bold(c_red("invalid"))
        if tuple_parsed_unit is not None:
            if tuple_parsed_unit[0] is not None:
                str_prefix = c_bold(c_yellow(tuple_parsed_unit[0]))
        str_unit_name = c_bold(c_red("invalid"))
        if tuple_parsed_unit is not None:
            if tuple_parsed_unit[1] is not None:
                str_unit_name = tuple_parsed_unit[1]
            else:
                str_unit_name = c_bold(c_cyan("null"))
        return (str_prefix, str_unit_name)

    for j in range(0, 4):
        print print_split
        print "  " + c_bold(c_cyan("Table %d")) % (j + 1)
        print print_split
        for obj_unit in unit_tables(ureg)[j]:
            str_prefix, str_unit_name = parse_unit_with_color(obj_unit)
            print "  " + (c_bold("%s") + " - %s, %s") % (
                obj_unit,
                str_prefix,
                str_unit_name
            )

    print print_split
    print "  " + c_bold(c_yellow("Supported Prefixes"))
    print print_split
    for multiplier, str_prefix in sorted(prefixes.items()):
        print "  " + (c_bold("%s") + " = %.2e") % (str_prefix, multiplier)

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
    print "  " + c_bold(c_yellow("Prefixed Units"))
    print print_split
    for obj_unit in units_prefixed:
        str_prefix, str_unit_name = parse_unit_with_color(obj_unit)
        print "  " + (c_bold("%s") + " - %s, %s") % (
            obj_unit,
            str_prefix,
            str_unit_name
        )

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
    print "  " + c_bold(c_red("Invalid Units"))
    print print_split
    for obj_unit in units_invalid:
        str_prefix, str_unit_name = parse_unit_with_color(obj_unit)
        print "  " + (c_bold("%s") + " - %s, %s") % (
            obj_unit,
            str_prefix,
            str_unit_name
        )

    print print_split

main()
