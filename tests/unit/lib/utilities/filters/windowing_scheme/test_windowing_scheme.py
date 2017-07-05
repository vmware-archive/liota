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

import time
import unittest

from liota.lib.utilities.filters.range_filter import RangeFilter, Type
from liota.lib.utilities.filters.windowing_scheme.windowing_scheme import WindowingScheme


class WindowingSchemeTest(unittest.TestCase):
    """
    Unit test cases for Windowing Scheme
    """
    def setUp(self):
        """Initialize lower bound, upper bound and a filter for Windowing scheme test"""
        self.lower_bound = 10
        self.upper_bound = 20
        self.middle_value = (self.lower_bound + self.upper_bound)/2
        self.more_than_upper_bound = self.upper_bound + 10
        self.window_test_filter = RangeFilter(Type.CLOSED, self.lower_bound, self.upper_bound)

    def test_init_windowing_scheme_filter(self):
        """If filter not provided in Windowing scheme, raise TypeError"""
        self.assertRaises(TypeError, lambda: WindowingScheme("", 10))

    def test_init_windowing_scheme_window_size(self):
        """If window size is not a non negative number, raise ValueError"""
        self.assertRaises(ValueError, lambda: WindowingScheme(self.window_test_filter, "10"))
        self.assertRaises(ValueError, lambda: WindowingScheme(self.window_test_filter, -10))

    def test_window_filter(self):
        """If filter returns a valid value, windowing_scheme should return it"""
        test_window_scheme = WindowingScheme(self.window_test_filter, 5)
        filtered_value = test_window_scheme.filter(self.middle_value)
        self.assertEquals(filtered_value, self.middle_value)

    """
    Tests for next window time has elapsed
        1. With no sample passed
        2. At least one sample passed
    """
    def test_next_window_time_no_sample_passed(self):
        """If next window time has elapsed with no sample passed so far then pass collected value"""
        test_window_scheme = WindowingScheme(self.window_test_filter, 3)
        time.sleep(4)
        collected_value = test_window_scheme.filter(self.more_than_upper_bound)
        self.assertEquals(collected_value, self.more_than_upper_bound)

    def test_next_window_time_sample_passed(self):
        """If next window time has elapsed with at least one sample passed then pass filtered value"""
        test_window_scheme = WindowingScheme(self.window_test_filter, 3)
        # Value 15 will be filtered as it ranges between lower and upper bound limits
        filtered_value = test_window_scheme.filter(self.middle_value)
        self.assertEquals(filtered_value, self.middle_value)
        # Let next window time elapse
        time.sleep(4)
        filtered_value = test_window_scheme.filter(self.more_than_upper_bound)
        # None is expected as filtered value because at least one sample has been already passed and
        # value ranges outside lower and upper bound limits
        self.assertEquals(filtered_value, None)

if __name__ == '__main__':
    unittest.main(verbosity=1)
