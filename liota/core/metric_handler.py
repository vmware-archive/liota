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

from Queue import Queue, PriorityQueue, Full
import heapq
import inspect
import logging
from threading import Thread, Condition
from time import time as _time

from liota.utilities.utility import getUTCmillis

log = logging.getLogger(__name__)

event_ds = None
collect_queue = None
send_queue = None
event_checker_thread = None
send_thread = None

class EventsPriorityQueue(PriorityQueue):
    def __init__(self):
        PriorityQueue.__init__(self)
        self.first_element_changed = Condition(self.mutex)

    def put_and_notify(self, item, block=True, timeout=None):
        log.info("Adding Event:" + str(item))
        self.not_full.acquire()
        try:
            first_element_before_insertion = None
            if self._qsize() > 0:
                first_element_before_insertion = heapq.nsmallest(1, self.queue)[0]

            if self.maxsize > 0:
                if not block:
                    if self._qsize() == self.maxsize:
                        raise Full
                elif timeout is None:
                    while self._qsize() == self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
                else:
                    endtime = _time() + timeout
                    while self._qsize() == self.maxsize:
                        remaining = endtime - _time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()

            first_element_after_insertion = heapq.nsmallest(1, self.queue)[0]
            if first_element_before_insertion != first_element_after_insertion:
                self.first_element_changed.notify()
        finally:
            self.not_full.release()

    def get_next_element_when_ready(self):
        self.first_element_changed.acquire()
        try:
            isNotReady = True
            while isNotReady:
                if self._qsize() > 0:
                    first_element = heapq.nsmallest(1, self.queue)[0]
                    timeout = (first_element.get_next_run_time() - getUTCmillis()) / 1000.0
                    log.info("Waiting on acquired first_element_changed LOCK for: " + str(timeout))
                    self.first_element_changed.wait(timeout)
                else:
                    self.first_element_changed.wait()
                    first_element = heapq.nsmallest(1, self.queue)[0]
                if (first_element.get_next_run_time() - getUTCmillis()) <= 0:
                    isNotReady = False
                    first_element = self._get()
            return first_element
        finally:
            self.first_element_changed.release()

class EventCheckerThread(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.start()

    def run(self):
        log.info("Started EventCheckerThread")
        global event_ds
        global collect_queue
        while True:
            log.debug("Waiting for event...")
            matric = event_ds.get_next_element_when_ready()
            log.debug("Got event:" + str(matric))
            collect_queue.put(matric)

class SendThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()

    def run(self):
        log.info("Started SendThread")
        global send_queue
        while True:
            log.info("Waiting to send...")
            matric = send_queue.get()
            log.info("Got item in send_queue:" + str(matric))
            matric.send_data()

class CollectionThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        global event_ds
        global collect_queue
        global send_queue
        while True:
            matric = collect_queue.get()
            log.info("Collecting stats for matric:" + str(matric))
            try:
                matric.collect()
                matric.set_next_run_time()
                event_ds.put_and_notify(matric)
                if matric.is_ready_to_send():
                    send_queue.put(matric)
            except Exception as e:
                log.error(e)

class CollectionThreadPool:
    def __init__(self, num_threads):
        log.info("Starting " + str(num_threads) + " for collection")
        for _ in range(num_threads): CollectionThread()

is_initialization_done = False

def initialize():
    global is_initialization_done
    if is_initialization_done:
        log.debug("Initialization already done")
        pass
    else:
        log.debug("Initializing.............")
        global event_ds
        if event_ds == None:
            event_ds = EventsPriorityQueue()
        global event_checker_thread
        if event_checker_thread == None:
            event_checker_thread = EventCheckerThread()
        global collect_queue
        if collect_queue == None:
            collect_queue = Queue()
        global send_queue
        if send_queue == None:
            send_queue = Queue()
        global send_thread
        if send_thread == None:
            send_thread = SendThread()
        pool = CollectionThreadPool(20)  # TODO: Make pool size configurable
        is_initialization_done = True

class Metric(object):

        def __init__(self, gw, details, unit, sampling_interval_sec, aggregation_size, sampling_function, data_center_component):
            self.data_center_component = data_center_component
            self.gw = gw
            self.details = details
            self.unit = unit
            self.sampling_interval_sec = sampling_interval_sec
            self.aggregation_size = aggregation_size
            self.current_aggregation_size = 0
            self.sampling_function = sampling_function
            self.values = []

        def __str__(self, *args, **kwargs):
            return str(self.details) + ":" + str(self.next_run_time)

        def __cmp__(self, other):
            if other == None:
                return -1
            if not isinstance(other, Metric):
                return -1
            return cmp(self.next_run_time, other.next_run_time)

        def write_full(self, t, v):
            self.values.append((t, v))

        def write_map_values(self, v):
            self.write_full(getUTCmillis(), v)

        def get_next_run_time(self):
            return self.next_run_time

        def set_next_run_time(self):
            self.next_run_time = self.next_run_time + (self.sampling_interval_sec * 1000)
            log.info("Set next run time to:" + str(self.next_run_time))

        def start_collecting(self):
            # TODO: Add a check to ensure that start_collecting for a metric is called only once by the client code
            initialize()
            global event_ds
            self.next_run_time = getUTCmillis() + (self.sampling_interval_sec * 1000)
            event_ds.put_and_notify(self)

        def is_ready_to_send(self):
            log.debug("self.current_aggregation_size:" + str(self.current_aggregation_size))
            log.debug("self.aggregation_size:" + str(self.aggregation_size))
            return self.current_aggregation_size >= self.aggregation_size

        def collect(self):
            log.debug("Collecting values for the resource {0} ".format(self.details))
            self.args_required = len(inspect.getargspec(self.sampling_function)[0])
            if self.args_required is not 0:
                self.cal_value = self.sampling_function(1)
            else:
                self.cal_value = self.sampling_function()
            log.info("{0} Sample Value: {1}".format(self.details, self.cal_value))
            log.debug("Size of the list {0}".format(len(self.values)))
            self.write_map_values(self.cal_value)
            self.current_aggregation_size = self.current_aggregation_size + 1

        def send_data(self):
            log.info("Publishing values {0} for the resource {1} ".format(self.values, self.details))
            if not self.values:
                # No values measured since last report_data
                return True
            self.data_center_component.publish(self)
            self.values[:] = []
            self.current_aggregation_size = 0

