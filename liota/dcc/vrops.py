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

import inspect
import json
import logging
import sched, time
import signal
from socket import timeout
import sys
import threading
from time import timezone

from cloud_provider_base import CloudProvider
from helix_protocol import HelixProtocol
from liota.utilities.utility import getUTCmillis

log = logging.getLogger(__name__)

class Vrops(CloudProvider):
    """ The implementation of vROPS cloud provider soultion

    """
    def __init__(self, username, password, con):
        log.info("Logging into DCC")
        self.con = con
        self.username = username
        self.password = password
        self.proto = HelixProtocol(self.con, username, password)
        self.resource_uuid = "null"
        def on_receive_safe(msg):
            try:
                log.debug("Received msg: {0}".format(msg))
                json_msg = json.loads(msg)
                self.proto.on_receive(json.loads(msg))
                log.debug("Processed msg: {0}".format(json_msg["type"]))
                if (json_msg["type"] == "connection_verified"):
                    log.info("Verified")
                    exit()
            except Exception:
                raise
                log.exception("Error received on connecting to DCC instance. Please verify the credentials and try again.")


        thread = threading.Thread(target=self.con.run)
        self.con.on_receive = on_receive_safe
        thread.daemon = True
        thread.start()
        thread.join()
        log.info("Logged in to DCC successfully")

    def register(self, gw):
        """ Register the objects

        """
        if gw.res_uuid == None:
            log.info("Creating resource")
            log.info("Resource Name: {0}".format(gw.res_name))
            def on_receive_safe(msg):
                try:
                    log.debug("Received msg: {0}".format(msg))
                    if msg != "":
                       json_msg = json.loads(msg)
                       self.proto.on_receive(json.loads(msg))
                       log.debug("Processed msg: {0}".format(json_msg["type"]))
                       if (json_msg["type"] == "create_or_find_resource_response") :
                           if json_msg["body"]["uuid"] != "null":
                               log.info("FOUND RESOURCE: {0}".format(json_msg["body"]["uuid"]))
                               gw.res_uuid = json_msg["body"]["uuid"]
                               time.sleep(5)
                               exit()
                           else:
                               log.info("Waiting for resource creation")
                               time.sleep(5)
                               self.con.send(self.registration(self.con.next_id(), gw.identifier, gw.res_name, gw.res_kind))
                except:
                    raise
            thread = threading.Thread(target=self.con.run)
            self.con.on_receive = on_receive_safe
            thread.daemon = True
            thread.start()
            self.con.send(self.registration(self.con.next_id(), gw.identifier, gw.res_name, gw.res_kind))
            thread.join()
            log.info("Resource Registered {0}".format(gw.res_name))
            gw.con = self.con
            if gw.parent is not None:
                self.init_relations(gw)
                log.info("Relationship Created")

    def connect_soc(self, protocol, url, user_name, password):
        pass

    def create_metric(self, gw, details, unit, value, sampling_interval_sec=10, report_interval_sec=30):
        return self.Metric(gw, details, unit, sampling_interval_sec, report_interval_sec, value, self)


    class Metric(object):
        """ Sub-class defined in order to create the metric and publish data
            after the defined report_interval_sec

        """
        def __init__(self, gw, details, unit, sampling_interval_sec, report_interval_sec, sample_function, vrops_object):
            self.vrops_object = vrops_object
            self.gw = gw
            self.details = details
            self.unit = unit
            self.sampling_interval_sec = sampling_interval_sec
            self.report_interval_sec = report_interval_sec
            self.sample_function = sample_function
            self.values = []
            signal.signal(signal.SIGINT, signal.SIG_IGN)

        def write_full(self, t, v):
            self.values.append((t, v))

        def write_map_values(self, v):
            self.write_full(getUTCmillis(), v)

        def start_collecting(self):
            """ This function starts the thread in order to collect stats

            """
            if self.gw.res_uuid != None:
                executor = threading.Thread(target=self.execute)
                executor.start()
                threading.Timer(self.report_interval_sec, self.report_data).start()

        def execute(self):
            try:
                while True:
                    log.debug("Collecting values for the resource {0} {1}".format(self.details, self.gw.res_name))
                    self.args_required = len(inspect.getargspec(self.sample_function)[0])
                    if self.args_required is not 0:
                        self.cal_value = self.sample_function(1)
                    else:
                        self.cal_value = self.sample_function()
                    log.debug("{0} Sample Value: {1}".format(self.details, self.cal_value))
                    log.debug("Size of the list {0}".format(len(self.values)))
                    self.write_map_values(self.cal_value)
                    # Batch processing if required
                    # if len(self.values) == 6:
                    #    self.report_data()
                    time.sleep(self.sampling_interval_sec)
            except Exception:
                log.exception("Error while collecting values for metrics.")

        def report_data(self):
            """ This function published the sample values onto the cloud_provider solution

            """
            threading.Timer(self.report_interval_sec, self.report_data).start()
            log.info("Publishing values for the resource {0} {1}".format(self.details, self.gw.res_name))
            if not self.values:
                # No values measured since last report_data
                return True
            timestamps = [t for t, _ in self.values]
            values = [v for _, v in self.values]
            update = self.gw._report_data(self.vrops_object.con.next_id(), self.details, timestamps, values)
            self.vrops_object.con.send(update)
            self.values[:] = []

    def subscribe(self):
        pass

    # TO DO: To be implemented later if required
    def publish(self, sample):
        pass

    def init_relations(self, gw):
      """ This function initializes all relations between gateway and it's children.
          It is called after each object's UUID is received.

          Parameters:
          - obj: The object that has just obtained an UUID

      """
      self.con.send(gw._create_relationship(self.con.next_id(), gw.parent))


    def registration(self, msg_id, res_id, res_name, res_kind):
      return {
         "transactionID": msg_id,
         "type": "create_or_find_resource_request",
         "body": {
            "kind": res_kind,
            "id": res_id,
            "name": res_name
         }
      }


