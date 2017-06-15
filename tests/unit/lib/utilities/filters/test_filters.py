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

import unittest

from liota.lib.utilities.filters.range_filter import RangeFilter, Type


class RangeFilterTest(unittest.TestCase):
    """
    Range Filter Unit Test Cases
    """
    def setUp(self):
        """Initialize lower and upper bound for filter test"""
        self.lower_bound = 10
        self.upper_bound = 20
        self.less_than_lower_bound = self.lower_bound - 10
        self.middle_value = (self.lower_bound + self.upper_bound) / 2
        self.more_than_upper_bound = self.upper_bound + 10

    def test_init_filter_type (self):
        """If invalid filter type, raise TypeError"""
        self.assertRaises(TypeError, lambda: RangeFilter(None, 0, 1))

    def test_init_lower_upper_bound(self):
        """If both lower and upper bound is not a number, raise TypeError"""
        self.assertRaises(TypeError, lambda: RangeFilter(Type.CLOSED, "0", "1"))

    def test_init_lower_bound(self):
        """If lower bound is not a number, raise TypeError"""
        self.assertRaises(TypeError, lambda: RangeFilter(Type.CLOSED, "0", 1))

    def test_init_upper_bound(self):
        """If upper bound is not a number, raise TypeError"""
        self.assertRaises(TypeError, lambda: RangeFilter(Type.CLOSED, 1, "2"))

    def test_init_lower_less_than(self):
        """In filter LESS_THAN if lower bound is not a number, raise TypeError"""
        self.assertRaises(TypeError, lambda: RangeFilter(Type.LESS_THAN, "0", 1))

    def test_init_upper_greater_than(self):
        """In filter GREATER_THAN if upper bound is not a number, raise TypeError"""
        self.assertRaises(TypeError, lambda: RangeFilter(Type.GREATER_THAN, 1, "2"))

    """
    Accept filters : Bounded at both end
    Values : Ranging inside limit
    """
    def test_number_closed(self):
        """If any filter applied on value which is not a number, value will be returned as it is"""
        closed_filter = RangeFilter(Type.CLOSED, self.lower_bound, self.upper_bound)
        value = closed_filter.filter("6")
        self.assertEquals(value, "6")

    def test_closed_filter(self):
        """If CLOSED filter applied value will be accepted if: lower_bound <= value <= upper_bound"""
        closed_filter = RangeFilter(Type.CLOSED, self.lower_bound, self.upper_bound)
        value = closed_filter.filter(self.middle_value)
        self.assertEquals(value, self.middle_value)

    def test_open_filter(self):
        """If OPEN filter applied value will be accepted if: lower_bound < value < upper_bound"""
        open_filter = RangeFilter(Type.OPEN, self.lower_bound, self.upper_bound)
        out_range_value = open_filter.filter(self.lower_bound)
        in_range_value = open_filter.filter(self.middle_value)
        self.assertEquals(out_range_value, None)
        self.assertEquals(in_range_value, self.middle_value)

    def test_closed_open_filter(self):
        """If CLOSED_OPEN filter applied value will be accepted if: lower_bound <= value < upper_bound """
        closed_open_filter = RangeFilter(Type.CLOSED_OPEN, self.lower_bound, self.upper_bound)
        out_range_value = closed_open_filter.filter(self.upper_bound)
        in_range_value = closed_open_filter.filter(self.lower_bound)
        self.assertEquals(out_range_value, None)
        self.assertEquals(in_range_value, self.lower_bound)

    def test_open_closed_filter(self):
        """If OPEN_CLOSED filter applied value will be accepted if: lower_bound < value <= upper_bound """
        open_closed_filter = RangeFilter(Type.OPEN_CLOSED, self.lower_bound, self.upper_bound)
        out_range_value = open_closed_filter.filter(self.lower_bound)
        in_range_value = open_closed_filter.filter(self.upper_bound)
        self.assertEquals(out_range_value, None)
        self.assertEquals(in_range_value, self.upper_bound)

    """
    Reject filters : Bounded at both end
    Values : Ranging outside limit
    """
    def test_closed_reject(self):
        """If CLOSED_REJECT filter applied value will be discarded if: lower_bound <= value <= upper_bound"""
        closed_reject_filter = RangeFilter(Type.CLOSED_REJECT, self.lower_bound, self.upper_bound)
        out_range_value = closed_reject_filter.filter(self.more_than_upper_bound)
        in_range_value = closed_reject_filter.filter(self.lower_bound)
        self.assertEquals(out_range_value, self.more_than_upper_bound)
        self.assertEquals(in_range_value, None)

    def test_open_reject(self):
        """If OPEN_REJECT filter applied value will be discarded if: lower_bound < value < upper_bound"""
        open_reject_filter = RangeFilter(Type.OPEN_REJECT, self.lower_bound, self.upper_bound)
        out_range_value = open_reject_filter.filter(self.lower_bound)
        in_range_value = open_reject_filter.filter(self.middle_value)
        self.assertEquals(out_range_value, self.lower_bound)
        self.assertEquals(in_range_value, None)

    def test_closed_open_reject(self):
        """If CLOSED_OPEN_REJECT filter applied value will be discarded if: lower_bound <= value < upper_bound"""
        closed_open_reject = RangeFilter(Type.CLOSED_OPEN_REJECT, self.lower_bound, self.upper_bound)
        out_range_value = closed_open_reject.filter(self.upper_bound)
        in_range_value = closed_open_reject.filter(self.lower_bound)
        self.assertEquals(out_range_value, self.upper_bound)
        self.assertEquals(in_range_value, None)

    def test_open_closed_reject(self):
        """If OPEN_CLOSED_REJECT filter applied value will be discarded if: lower_bound < value <= upper_bound"""
        open_closed_reject = RangeFilter(Type.OPEN_CLOSED_REJECT, self.lower_bound, self.upper_bound)
        out_range_value = open_closed_reject.filter(self.lower_bound)
        in_range_value = open_closed_reject.filter(self.upper_bound)
        self.assertEquals(out_range_value, self.lower_bound)
        self.assertEquals(in_range_value, None)

    """
    Filters bounded at one end
    """
    def test_less_than(self):
        """If LESS_THAN filter applied value will be accepted if: value < lower_bound"""
        less_than_filter = RangeFilter(Type.LESS_THAN, self.lower_bound, self.upper_bound)
        out_range_value = less_than_filter.filter(self.lower_bound)
        in_range_value = less_than_filter.filter(self.less_than_lower_bound)
        self.assertEquals(out_range_value, None)
        self.assertEquals(in_range_value, self.less_than_lower_bound)

    def test_at_most(self):
        """If AT_MOST filter applied value will be accepted if: value <= lower_bound"""
        at_most_filter = RangeFilter(Type.AT_MOST, self.lower_bound, self.upper_bound)
        out_range_value = at_most_filter.filter(self.upper_bound)
        in_range_value = at_most_filter.filter(self.less_than_lower_bound)
        self.assertEquals(out_range_value, None)
        self.assertEquals(in_range_value, self.less_than_lower_bound)

    def test_greater_than(self):
        """If GREATER_THAN filter applied value will be accepted if: value > upper_bound"""
        greater_than_filter = RangeFilter(Type.GREATER_THAN, self.lower_bound, self.upper_bound)
        out_range_value = greater_than_filter.filter(self.upper_bound)
        in_range_value = greater_than_filter.filter(self.more_than_upper_bound)
        self.assertEquals(out_range_value, None)
        self.assertEquals(in_range_value, self.more_than_upper_bound)

    def test_at_least(self):
        """If AT_LEAST filter applied value will be accepted if: value >= upper_bound"""
        at_least_filter = RangeFilter(Type.AT_LEAST, self.lower_bound, self.upper_bound)
        out_range_value = at_least_filter.filter(self.less_than_lower_bound)
        in_range_value = at_least_filter.filter(self.more_than_upper_bound)
        self.assertEquals(out_range_value, None)
        self.assertEquals(in_range_value, self.more_than_upper_bound)

if __name__ == '__main__':
    unittest.main(verbosity=1)
