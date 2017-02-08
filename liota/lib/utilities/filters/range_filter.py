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
from numbers import Number

from aenum import UniqueEnum

from liota.lib.utilities.filters.filter import Filter

log = logging.getLogger(__name__)


class Type(UniqueEnum):
    """
    Enum for different filter-types supported by RangeFilter

    ** Accept Filters:
        *  CLOSED       - [1, 10] values from 1...10 are accepted
        *  OPEN         - (1, 10) values from 2...9 are accepted
        *  CLOSED_OPEN  - [1, 10) values from 1...9 are accepted
        *  OPEN_CLOSED  - (1, 10] values from 2...10 are accepted

    ** Reject Filters:
        *  CLOSED_REJECT        - [1, 10] values from 1...10 are rejected
        *  OPEN_REJECT          - (1, 10) values from 2...9 are rejected
        *  CLOSED_OPEN_REJECT   - [1, 10) values from 1...9 are rejected
        *  OPEN_CLOSED_REJECT   - (1, 10] values from 2...10 are rejected

    ** Filters bounded at one end:
        *  LESS_THAN    -  values < 1 are accepted
        *  AT_MOST      -  values <= 1 are accepted
        *  GREATER_THAN -  values > 10 are accepted
        *  AT_LEAST     -  values >= 10 are accepted
    """
    #  Accept filters - bounded at both ends
    CLOSED = 0
    OPEN = 1
    CLOSED_OPEN = 2
    OPEN_CLOSED = 3
    #  Reject filters - bounded at both ends
    CLOSED_REJECT = 4
    OPEN_REJECT = 5
    CLOSED_OPEN_REJECT = 6
    OPEN_CLOSED_REJECT = 7
    #  Filters - bounded at one end
    LESS_THAN = 8
    AT_MOST = 9
    GREATER_THAN = 10
    AT_LEAST = 11


class RangeFilter(Filter):
    """
    A simple lightweight filter, that filters values based on the specified filter type (range).
    """

    def __init__(self, filter_type, lower_bound, upper_bound):
        """
        :param filter_type: Any one type from Filter Enum.
        :param lower_bound: Lower bound
        :param upper_bound: Upper bound
        """
        if filter_type not in Type:
            log.error("Unsupported Filter Type.")
            raise TypeError("Unsupported Filter Type.")

        self.filter_type = filter_type
        self._validate(lower_bound, upper_bound)
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def _validate(self, lower_bound, upper_bound):
        """
        Validation of lower_bound and upper_bound value for the specified filter_type.

        :param lower_bound: Lower bound
        :param upper_bound: Upper bound
        :return: None
        """

        if self.filter_type in [Type.CLOSED, Type.OPEN, Type.CLOSED_OPEN, Type.OPEN_CLOSED,
                                Type.CLOSED_REJECT, Type.OPEN_REJECT, Type.CLOSED_OPEN_REJECT,
                                Type.OPEN_CLOSED_REJECT] and \
                (not isinstance(lower_bound, Number) or not isinstance(upper_bound, Number)):
            log.error("Both lower_bound and upper_bound must be a number")
            raise TypeError("Both lower_bound and upper_bound must be a number")

        elif self.filter_type in [Type.LESS_THAN, Type.AT_MOST] and not isinstance(lower_bound, Number):
            log.error("lower_bound must be a number")
            raise TypeError("lower_bound must be a number")

        elif self.filter_type in [Type.GREATER_THAN, Type.AT_LEAST] and not isinstance(upper_bound, Number):
            log.error("upper_bound must be a number")
            raise TypeError("upper_bound must be a number")

    def filter(self, v):
        """
        RangeFilter Implementation. Performs filtering based on specified filter_type.

        :param v: Collected value
        :return: Filtered value or None
        """
        result = None
        log.info("Applying RangeFilter " + str(self.filter_type))
        if not isinstance(v, Number):
            log.warn("Value is not a number. Returning without applying filter")
            return v

        # Accept filters - bounded at both ends
        elif self.filter_type is Type.CLOSED and (self.lower_bound <= v <= self.upper_bound):
            result = v

        elif self.filter_type is Type.OPEN and (self.lower_bound < v < self.upper_bound):
            result = v

        elif self.filter_type is Type.CLOSED_OPEN and (self.lower_bound <= v < self.upper_bound):
            result = v

        elif self.filter_type is Type.OPEN_CLOSED and (self.lower_bound < v <= self.upper_bound):
            result = v

        # Reject filters - bounded at both ends
        elif self.filter_type is Type.CLOSED_REJECT and (not self.lower_bound <= v <= self.upper_bound):
            result = v

        elif self.filter_type is Type.OPEN_REJECT and (not self.lower_bound < v < self.upper_bound):
            result = v

        elif self.filter_type is Type.CLOSED_OPEN_REJECT and (not self.lower_bound <= v < self.upper_bound):
            result = v

        elif self.filter_type is Type.OPEN_CLOSED_REJECT and (not self.lower_bound < v <= self.upper_bound):
            result = v

        # Filters - bounded at one end
        elif self.filter_type is Type.LESS_THAN and (v < self.lower_bound):
            result = v

        elif self.filter_type is Type.AT_MOST and (v <= self.lower_bound):
            result = v

        elif self.filter_type is Type.GREATER_THAN and (v > self.upper_bound):
            result = v

        elif self.filter_type is Type.AT_LEAST and (v >= self.upper_bound):
            result = v

        if result is not None:
            log.info("Value passed by filter : %s" % str(result))
        else:
            log.info("Value rejected by filter : %s" % str(v))

        return result
