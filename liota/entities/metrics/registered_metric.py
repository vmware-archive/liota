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
    """
    RegisteredMetric implementation.

    This class provides APIs to control collection of Metrics.

    Collected Metric values are stored in a Queue as (timestamp, value) pairs till the aggregation size is reached.
    """

    def __init__(self, ref_metric, ref_dcc, reg_entity_id):
        """
        Init method for RegisteredMetric.

        :param ref_metric: Metric that is represented by a RegisteredMetric Object
        :param ref_dcc: DCC with which the Metric is registered with
        :param reg_entity_id: RegisteredEntity ID
        """
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
        Starts metric collection through MetricHandler.
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
        Stops metric collection by marking metric as dead.

        :return:
        """
        self.flag_alive = False
        log.debug("Metric %s is marked for deletion" %
                 str(self.ref_entity.name))

    def add_collected_data(self, collected_data):
        """
        Adds collected data to the Queue as (timestamp, value) tuple.

        :param collected_data: It MUST be one of the following:
                              - List of (timestamp, value) tuples
                              - (timestamp, value) tuple
                              - value

        :return: Number of data points collected in Integer
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
        Returns the upcoming time when a Metric must be collected in milliseconds.
        :return: time in milliseconds
        """
        return self._next_run_time

    def set_next_run_time(self):
        """
        Sets the upcoming time when a Metric must be collected in milliseconds.
        :return:
        """
        self._next_run_time = self._next_run_time + \
            (self.ref_entity.interval * 1000)
        log.debug("Set next run time to:" + str(self._next_run_time))

    def is_ready_to_send(self):
        """
        Returns whether collected metrics should be published or not based on the current queue size
        and the specified aggregation size.

        :return: boolean true or false
        """
        log.debug("self.current_aggregation_size:" +
                  str(self.current_aggregation_size))
        log.debug("self.aggregation_size:" +
                  str(self.ref_entity.aggregation_size))
        return self.current_aggregation_size >= self.ref_entity.aggregation_size

    def collect(self):
        """
        Collects metric by invoking the sampling function.

        It is the responsibility of the user to make sure that sampling function doesn't through error or block indefinitely.

        'None' values returned by sampling functions will be ignored.
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
        Resets current aggregation size
        :return:
        """
        self.current_aggregation_size = 0

    def send_data(self):
        """
        Sends the RegisteredMetric to DCC so that it can publish the data
        :return:
        """
        log.info("Publishing values for the resource {0} ".format(
            self.ref_entity.name))
        if not self.values:
            # No values measured since last report_data
            return True
        try:
            self.ref_dcc.publish(self)
        except Exception:
            log.error("Exception while publishing message", exc_info=True)

    def __str__(self, *args, **kwargs):
        """
        Overridden toString method implementation for RegisteredMetric object.
        :param args:
        :param kwargs:
        :return:
        """
        return str(self.ref_entity.name) + ":" + str(self._next_run_time)

    def __cmp__(self, other):
        """
        Overridden Comparator method implementation for RegisteredMetric based on _next_run_time.
        :param other: Other Object to be compared with this RegisteredMetric Object
        :return:
        """
        if other is None:
            return -1
        if not isinstance(other, RegisteredMetric):
            return -1
        return cmp(self._next_run_time, other._next_run_time)
