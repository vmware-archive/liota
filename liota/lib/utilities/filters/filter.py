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

from abc import ABCMeta, abstractmethod
from numbers import Number
from liota.lib.utilities.utility import getUTCmillis
import logging

log = logging.getLogger(__name__)


class Filter:
    """
    Abstract base class for all Filters.

    Filtering can reduce network bandwidth by trimming off data that we are not interested in.  Also, most of the
    time systems will be working normally.  Sending all those normal data to DCC is not desired most of the time,
    as there is always storage and processing overhead involved.

    All abnormal data will be sent and if there is no abnormality, a heartbeat (single value of normal data) will be
    sent so that DCC can know system is working normally.

    Filter keeps track of a configurable time window. Heartbeat is sent at the end of every time window.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, window_size_sec):

        if not isinstance(window_size_sec, Number) or window_size_sec < 0:
            log.error("window_size_sec must be a non negative number")
            raise ValueError("window_size_sec must be a non negative number")

        self.window_size_sec = window_size_sec
        self.sample_passed = True
        self.next_window_time = 0

    def filter(self, collected_data):
        """
        Uses _filter() to apply appropriate filter logic.

        :param collected_data: Data collected by sampling function.
                               Currently supported types are: list of (ts, v) or (ts, v) or v

        :return: Filtered data of corresponding type or None
        """
        if collected_data is None:
            return

        filtered_data = None

        # collected_data is list of (ts, v)
        if isinstance(collected_data, list):
            filtered_data = []
            for ts, v in collected_data:
                if self._filter(v) is not None:
                    filtered_data.append((ts, v))
        # collected_data is (ts, v)
        elif isinstance(collected_data, tuple):
            if self._filter(collected_data[1]) is not None:
                filtered_data = collected_data
        # collected_data is v
        else:
            if self._filter(collected_data) is not None:
                filtered_data = collected_data

        # Next window time has elapsed.
        if getUTCmillis() >= self.next_window_time:
            #  At-least one sample has not passed so far during this window.
            if not self.sample_passed and (filtered_data is None or
                                               (isinstance(filtered_data, list) and len(filtered_data) == 0)):
                self._set_next_window_time()
                log.info("Sending heartbeat for this window.")
                if isinstance(collected_data, list):
                    return [(collected_data[-1])]  # latest element from original list
                else:
                    return collected_data  # (ts, v) or v

            # At-least one sample has (or will be) passed by now.
            else:
                self._set_next_window_time()
                if isinstance(filtered_data, list) and len(filtered_data) == 0:
                    return
                return filtered_data  # Could be filtered-value or None

        # Next window time has not elapsed.
        else:
            if isinstance(filtered_data, list) and len(filtered_data) > 0:
                self.sample_passed = True  # At-least one sample has passed during this window
                return filtered_data
            elif not isinstance(filtered_data, list) and filtered_data is not None:
                self.sample_passed = True  # At-least one sample has passed during this window
                return filtered_data
            #  If none of the above match, None is returned

    @abstractmethod
    def _filter(self, v):
        """
        Child classes must implement appropriate filtering logic.

        :param v: value
        :return: v or None
        """
        pass

    def _set_next_window_time(self):
        """
        Sets next time-window for heartbeat.
        :return: None
        """
        self.next_window_time = getUTCmillis() + (self.window_size_sec * 1000)
        log.info("Resetting window")
        self.sample_passed = False  # Resetting
