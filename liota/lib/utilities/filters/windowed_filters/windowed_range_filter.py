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

import logging

from liota.lib.utilities.filters.range_filter import RangeFilter
from liota.lib.utilities.filters.windowed_filters.windowed_filter import WindowedFilter

log = logging.getLogger(__name__)


class WindowedRangeFilter(RangeFilter, WindowedFilter):
    """
    RangeFilter with windowing scheme.

    It keeps track of a configurable time window.  Even if all values has been filtered out at the
    end of every time window, collected value is returned so that DCC is aware of it.
    """

    def __init__(self, filter_type=None, lower_bound=None, upper_bound=None, window_size_sec=10):
        """
        :param filter_type: Any one type from Filter Enum of RangeFilter.
        :param lower_bound: Lower bound
        :param upper_bound: Upper bound
        :param window_size_sec: Configurable time window for heartbeat
        """
        RangeFilter.__init__(self, filter_type, lower_bound, upper_bound)
        WindowedFilter.__init__(self, window_size_sec)

    def filter(self, v):
        """
        Child classes must implement appropriate filtering logic.

        :param v: Collected value by sampling function.
        :return: Filtered value or None
        """
        log.info("Applying WindowedRangeFilter")
        return self._window(v, super(WindowedRangeFilter, self).filter(v))
