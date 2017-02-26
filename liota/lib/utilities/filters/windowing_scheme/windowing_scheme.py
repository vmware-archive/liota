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

from abc import abstractmethod
from numbers import Number
import logging

from liota.lib.utilities.utility import getUTCmillis
from liota.lib.utilities.filters.filter import Filter

log = logging.getLogger(__name__)


class WindowingScheme(Filter):
    """
    Applies windowing scheme to a Filter.

    It keeps track of a configurable time window.  Even if all values has been filtered out at the
    end of every time window, collected value is returned so that DCC is aware of it.
    """

    def __init__(self, filter_obj, window_size_sec):
        """
        :param filter_obj: Filter object.
        :param window_size_sec: Window size in seconds.
        """

        if not isinstance(filter_obj, Filter):
            raise TypeError("Filter Object is expected")
        if not isinstance(window_size_sec, Number) or window_size_sec < 0:
            log.error("window_size_sec must be a non negative number")
            raise ValueError("window_size_sec must be a non negative number")
        self.filter_obj = filter_obj
        self.window_size_sec = window_size_sec
        #  To track whether at-least one sample has been passed after filtering within a window
        self.sample_passed = False
        self.next_window_time = getUTCmillis() + (self.window_size_sec * 1000)

    def filter(self, v):
        """
        Applies filter and windowing scheme.

        :param v: Collected value by sampling function.
        :return: Filtered value or None
        """
        log.info("Applying windowing scheme")
        return self._window(v, self.filter_obj.filter(v))

    def _window(self, collected_value, filtered_value):
        """
        Windowing scheme.

        :param collected_value: Collected value by sampling function.
        :param filtered_value: Filtered value by sampling function.
        :return: Filtered value (or) collected value at the end of every time window.
        """
        # Next window time has elapsed.
        if getUTCmillis() >= self.next_window_time:
            #  At-least one sample has not passed so far during this window.
            if not self.sample_passed and filtered_value is None:
                self._set_next_window_time()
                log.info("Sending collected value for this window.")
                return collected_value

            # At-least one sample has (or will be) passed by now.
            else:
                self._set_next_window_time()
                return filtered_value  # Could be filtered-value or None

        # Next window time has not elapsed.
        else:
            if filtered_value is not None:
                self.sample_passed = True  # At-least one sample has passed during this window
            return filtered_value

    def _set_next_window_time(self):
        """
        Sets next time-window.
        :return: None
        """
        self.next_window_time += (self.window_size_sec * 1000)
        log.debug("Resetting window")
        self.sample_passed = False  # Resetting
