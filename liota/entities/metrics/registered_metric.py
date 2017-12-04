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

from Queue import Queue
import inspect
import logging
from liota.core import metric_handler
from liota.entities.registered_entity import RegisteredEntity
from liota.lib.utilities.utility import getUTCmillis


log = logging.getLogger(__name__)


class RegisteredMetric(RegisteredEntity):

    def __init__(self, ref_metric, ref_dcc, reg_entity_id):
        super(RegisteredMetric, self).__init__(ref_entity=ref_metric,
                                  ref_dcc=ref_dcc,
                                  reg_entity_id=reg_entity_id)
        self.flag_alive = False
        self._next_run_time = None
        self.current_aggregation_size = 0
        # -------------------------------------------------------------------
        # Elements in this queue are (ts, v) pairs.
        #
        self.values = Queue()

    def start_collecting(self):
        """
        Start to collect data for the metric:
        initialize metric handler and put the metric's first event to events
        priority queue.
        :return:
        """
        self.flag_alive = True
        # TODO: Add a check to ensure that start_collecting for a metric is
        # called only once by the client code
        metric_handler.initialize()
        self._next_run_time = getUTCmillis() + (self.ref_entity.interval * 1000)
        metric_handler.event_ds.put_and_notify(self)

    def stop_collecting(self):
        """
        Stop collecting data for the metric.
        :return:
        """
        self.flag_alive = False
        log.debug("Metric %s is marked for deletion" %
                 str(self.ref_entity.name))

    def add_collected_data(self, collected_data):
        """
        For the metric, add collected data into values queue.
        :param collected_data: collected data which may be in the format
                of list, tuple, and single sampled value
        :return: the length of added data
        """
        if isinstance(collected_data, list):
            for data_sample in collected_data:
                self.values.put(data_sample)
            return len(collected_data)
        elif isinstance(collected_data, tuple):
            self.values.put(collected_data)
            return 1
        else:
            self.values.put((getUTCmillis(), collected_data))
            return 1

    def get_next_run_time(self):
        """
        Get next run time for the metric.
        :return: next run time
        """
        return self._next_run_time

    def set_next_run_time(self):
        """
        Set next run time for the metric.
        :return:
        """
        self._next_run_time = self._next_run_time + \
            (self.ref_entity.interval * 1000)
        log.debug("Set next run time to:" + str(self._next_run_time))

    def is_ready_to_send(self):
        """
        Check whether the metric is ready to send its collected data or not.
        :return: True or False
        """
        log.debug("self.current_aggregation_size:" +
                  str(self.current_aggregation_size))
        log.debug("self.aggregation_size:" +
                  str(self.ref_entity.aggregation_size))
        return self.current_aggregation_size >= self.ref_entity.aggregation_size

    def collect(self):
        """
        For the metric, call its sampling function to collect values for it,
        add formated collected data into data queue, and update current
        aggregation size.
        :return:
        """
        log.debug("Collecting values for the resource {0} ".format(
            self.ref_entity.name))
        self.args_required = len(inspect.getargspec(
            self.ref_entity.sampling_function)[0])
        if self.args_required is not 0:
            self.collected_data = self.ref_entity.sampling_function(1)
        else:
            self.collected_data = self.ref_entity.sampling_function()
        log.debug("Size of the queue {0}".format(self.values.qsize()))
        #  Sampling function might return 'None' because of filtering
        if self.collected_data is not None:
            log.info("{0} Sample Value: {1}".format(
                self.ref_entity.name, self.collected_data))
            no_of_values_added = self.add_collected_data(self.collected_data)
            self.current_aggregation_size = self.current_aggregation_size + no_of_values_added

    def reset_aggregation_size(self):
        """
        Reset the metric's current aggregation size to 0.
        :return:
        """
        self.current_aggregation_size = 0

    def send_data(self):
        """
        Send the metric's collected data out.
        :return:
        """
        log.info("Publishing values for the resource {0} ".format(
            self.ref_entity.name))
        if self.values.qsize() == 0:
            # No values measured since last report_data
            return True
        try:
            self.ref_dcc.publish(self)
        except Exception:
            log.error("Exception while publishing message", exc_info=True)

    def __str__(self, *args, **kwargs):
        return str(self.ref_entity.name) + ":" + str(self._next_run_time)

    def __cmp__(self, other):
        if other is None:
            return -1
        if not isinstance(other, RegisteredMetric):
            return -1
        return cmp(self._next_run_time, other._next_run_time)
