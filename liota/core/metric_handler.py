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
import logging
from threading import Thread, Condition, Lock
from time import time as _time

from liota.lib.utilities.utility import getUTCmillis
from liota.lib.utilities.utility import read_liota_config

log = logging.getLogger(__name__)

event_ds = None
collect_queue = None
send_queue = None
event_checker_thread = None
send_thread = None
collect_thread_pool = None


class EventsPriorityQueue(PriorityQueue):

    def __init__(self):
        PriorityQueue.__init__(self)
        self.first_element_changed = Condition(self.mutex)

    def put_and_notify(self, item, block=True, timeout=None):
        """
        Add event into events priority queue and notify thread waiting to get.
        :param item: the event to be added
        :param block: whether to block until the event is added
        :param timeout: if not block, how long wait at most to add event
        :return:
        """
        log.debug("Adding Event:" + str(item))
        self.not_full.acquire()
        try:
            first_element_before_insertion = None
            if self._qsize() > 0:
                first_element_before_insertion = self.queue[0]

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

            first_element_after_insertion = self.queue[0]
            if first_element_before_insertion != first_element_after_insertion:
                self.first_element_changed.notify()
        finally:
            self.not_full.release()

    def get_next_element_when_ready(self):
        """
        Get next event from events priority queue when it is ready:
        for SystemExit event and dead event, pop from queue immediately;
        for other active event, wait until next run time, then pop from queue.
        :return:
        """
        self.first_element_changed.acquire()
        try:
            isNotReady = True
            while isNotReady:
                if self._qsize() > 0:
                    first_element = self.queue[0]
                    if isinstance(first_element, SystemExit):
                        first_element = self._get()
                        break
                    if not first_element.flag_alive:
                        log.debug("Early termination of dead metric")
                        first_element = self._get()
                        break
                    timeout = (
                        first_element.get_next_run_time() - getUTCmillis()
                    ) / 1000.0
                    log.debug("Waiting on acquired first_element_changed LOCK "
                             + "for: %.2f" % timeout)
                    self.first_element_changed.wait(timeout)
                else:
                    self.first_element_changed.wait()
                    first_element = self.queue[0]
                if isinstance(first_element, SystemExit):
                    first_element = self._get()
                    break
                if (first_element.get_next_run_time() - getUTCmillis()) <= 0 \
                        or not first_element.flag_alive:
                    isNotReady = False
                    first_element = self._get()
            return first_element
        finally:
            self.first_element_changed.release()


class EventCheckerThread(Thread):

    def __init__(self, name=None):
        Thread.__init__(self, name=name)
        self.flag_alive = True
        self.start()

    def run(self):
        """
        The execution function of EventCheckerThread.
        Loop on events priority queue to get next ready event:
        for SystemExit event, kill the thread;
        for dead event, discard it;
        for active event, put it into collect queue for execution.
        :return:
        """
        log.info("Started EventCheckerThread")
        global event_ds
        global collect_queue
        while self.flag_alive:
            log.debug("Waiting for event...")
            metric = event_ds.get_next_element_when_ready()
            if isinstance(metric, SystemExit):
                log.debug("Got exit signal")
                break
            log.debug("Got event:" + str(metric))
            if not metric.flag_alive:
                log.debug("Discarded dead metric: %s" % str(metric))
                continue
            collect_queue.put(metric)
        log.info("Thread exits: %s" % str(self.name))


class SendThread(Thread):

    def __init__(self, name=None):
        Thread.__init__(self, name=name)
        self.flag_alive = True
        self.start()

    def run(self):
        """
        The execution function of SendThread.
        Loop on send queue to get next ready send task:
        for SystemExit, kill the thread;
        for dead metric task, discard it;
        for active metric task, send metric data out.
        :return:
        """
        log.info("Started SendThread")
        global send_queue
        while self.flag_alive:
            log.debug("Waiting to send...")
            metric = send_queue.get()
            if isinstance(metric, SystemExit):
                log.debug("Got exit signal")
                break
            log.debug("Got item in send_queue: " + str(metric))
            if not metric.flag_alive:
                log.debug("Discarded dead metric: %s" % str(metric))
                continue
            metric.send_data()
        log.info("Thread exits: %s" % str(self.name))


class CollectionThread(Thread):

    def __init__(self, worker_stat_lock, name=None):
        Thread.__init__(self, name=name)
        self.daemon = True
        self.working_obj = None
        self._worker_stat_lock = worker_stat_lock
        self.start()

    def run(self):
        """
        The execution function of CollectionThread.
        Loop on collect queue to get next ready collection task:
        for dead metric task, discard it;
        for active metric task, collect data for that metric, then put
            its next event into events priority queue; if its data is
            ready to send, put it into send queue and reset for next round.
        :return:
        """
        global event_ds
        global collect_queue
        global send_queue
        while True:
            metric = collect_queue.get()
            log.debug("Collecting stats for metric: " + str(metric))
            try:
                if not metric.flag_alive:
                    log.debug("Discarded dead metric: %s" % str(metric))
                    continue
                with self._worker_stat_lock:
                    self.working_obj = metric
                metric.collect()
                with self._worker_stat_lock:
                    self.working_obj = None
                if not metric.flag_alive:
                    log.debug("Discarded dead metric: %s" % str(metric))
                    continue
                metric.set_next_run_time()
                event_ds.put_and_notify(metric)
                if metric.is_ready_to_send():
                    send_queue.put(metric)
                    metric.reset_aggregation_size()
            except Exception as e:
                log.error("Error collecting data for metric" + str(metric))
                raise e


class CollectionThreadPool:

    def __init__(self, num_threads):
        self._num_threads = num_threads
        self._pool = []
        self._worker_stat_lock = Lock()

        log.info("Starting " + str(num_threads) + " for collection")
        for j in range(num_threads):
            self._pool.append(CollectionThread(
                self._worker_stat_lock,
                name="Collector-%d" % (j + 1)
            ))

    def get_num_threads(self):
        """
        Get the number of CollectionThread.
        :return: the number of CollectionThread
        """
        return self._num_threads

    def get_stats_working(self):
        """
        Get the status of threads:
        the number of working threads, the number of alive threads,
        the number of all the threads and the number of threads.
        :return: the status of threads
        """
        num_working = 0
        num_alive = 0
        num_all = 0
        with self._worker_stat_lock:
            for tref in self._pool:
                if not isinstance(tref, Thread):
                    continue
                num_all += 1
                if tref.isAlive():
                    num_alive += 1
                if not tref.working_obj is None:
                    num_working += 1
        return [num_working,
                num_alive,
                num_all,
                self._num_threads]

is_initialization_done = False


def initialize():
    """
    Initialization for metric handling:
    create events priority queue, collect queue, and send queue;
    spawn event check thread and send thread; and
    create collection thread pool.
    :return:
    """
    global is_initialization_done
    if is_initialization_done:
        log.debug("Initialization already done")
        pass
    else:
        log.debug("Initializing.............")
        global event_ds
        if event_ds is None:
            event_ds = EventsPriorityQueue()
        global event_checker_thread
        if event_checker_thread is None:
            event_checker_thread = EventCheckerThread(
                name="EventCheckerThread")
        global collect_queue
        if collect_queue is None:
            collect_queue = Queue()
        global send_queue
        if send_queue is None:
            send_queue = Queue()
        global send_thread
        if send_thread is None:
            send_thread = SendThread(name="SendThread")
        global collect_thread_pool
        collect_thread_pool_size = int(read_liota_config('CORE_CFG','collect_thread_pool_size')) 
        collect_thread_pool = CollectionThreadPool(collect_thread_pool_size)
        is_initialization_done = True


def terminate():
    """
    Terminate metric handling:
    signal events priority queue and send queue to exit;
    disable event check thread and send thread; and
    create collection thread pool.
    :return:
    """
    global event_checker_thread
    if event_checker_thread:
        event_checker_thread.flag_alive = False
    global send_thread
    if send_thread:
        send_thread.flag_alive = False
    global event_ds
    if event_ds:
        event_ds.put_and_notify(SystemExit(), timeout=0)
    global send_queue
    if send_queue:
        send_queue.put(SystemExit())
