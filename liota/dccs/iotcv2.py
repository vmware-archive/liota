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

import json
import logging
import time
import threading
import Queue
from threading import Lock

from liota.dccs.dcc import DataCenterComponent, RegistrationFailure, SetPropertiesFailure, CreateRelationshipFailure
from liota.entities.metrics.metric import Metric
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.entities.registered_entity import RegisteredEntity

log = logging.getLogger(__name__)

timeout = 300

class Request:
    def __init__(self, guid, operation_id, user_queue):
        self.guid = guid
        # assume operation_id will be unique in one process
        self.operation_id = operation_id
        self.user_queue = user_queue

class Iotcv2(DataCenterComponent):
    """ The implementation of VMware IoTC V2 Data Center Component

    """

    def __init__(self, con):
        log.info("Logging into IOTC V2 DCC")
        self.comms = con
        if not self.comms.identity.username:
            log.error("Username not found")
            raise ValueError("Username not found")
        elif not self.comms.identity.password:
            log.error("Password not found")
            raise ValueError("Password not found")
        thread = threading.Thread(target=self.comms.receive)
        thread.daemon = True
        # This thread will continuously run in background to receive response or actions from DCC
        thread.start()
        time.sleep(0.5)
        self.counter = 0

        self.recv_msg_queue = self.comms.userdata
        self.req_ops_lock = Lock()
        self.req_dict = {}
        thread = threading.Thread(target=self._dispatch_recvd_msg)
        thread.daemon = True
        # This thread will continuously run in background to check and dispatch received responses
        thread.start()

    def register(self, entity_obj):
        if isinstance(entity_obj, Metric):
            # reg_entity_id should be parent's one: not known here yet
            # will add in create_relationship();
            log.info("Registering metric {0} locally".format(entity_obj.name))
            return RegisteredMetric(entity_obj, self, None)
        else:
            log.info("Registering resource with IoTCV2 {0}".format(entity_obj.name))
            # register fun internal queue
            reg_resp_q = Queue.Queue()

            def on_response(msg, reg_resp_q):
                try:
                    log.debug("Received msg: {0}".format(msg))
                    json_msg = json.loads(msg)
                    log.debug("Processing msg: {0}".format(json_msg["type"]))
                    if json_msg["type"] == "registerMO_rsp" and json_msg["guid"] != "null" and \
                                    json_msg["guid"] == entity_obj.entity_id:
                        log.info("Received registration response for: {0}".format(json_msg["guid"]))
                        if json_msg["result"] == 'SUCCESS':
                            self.reg_entity_id = json_msg["guid"]
                    else:
                        log.info("Waiting for resource registration response")
                        on_response(reg_resp_q.get(True, timeout), reg_resp_q)
                except:
                    raise Exception("Exception while registering resource")

            # create and add register request into req_list (waiting list)
            operation_id = self.next_id()
            req = Request(entity_obj.entity_id, operation_id, reg_resp_q)
            log.info("operation_id:{0} req:{1}".format(operation_id, req))
            with self.req_ops_lock:
                self.req_dict.update({str(operation_id): req})
                log.info("operation_id:{0} req_dict:{1}".format(operation_id, self.req_dict))
            self.comms.send(json.dumps(
                self._registration(operation_id, entity_obj.entity_id, entity_obj.name, entity_obj.entity_type)))
            # block until there is an item available or timeout
            try:
                on_response(reg_resp_q.get(True, timeout), reg_resp_q)
            except:
                raise Exception("Exception while registering resource")

            if not self.reg_entity_id:
                raise RegistrationFailure()
            log.info("Resource Registered {0}".format(entity_obj.name))

            return RegisteredEntity(entity_obj, self, self.reg_entity_id)

    def create_relationship(self, reg_entity_parent, reg_entity_child):
        # sanity check: must be RegisteredEntity or RegisteredMetricRegisteredMetric
        if (not isinstance(reg_entity_parent, RegisteredEntity) \
                    and not isinstance(reg_entity_parent, RegisteredMetric)) \
                or (not isinstance(reg_entity_child, RegisteredEntity) \
                            and not isinstance(reg_entity_child, RegisteredMetric)):
            raise TypeError()

        reg_entity_child.parent = reg_entity_parent
        if isinstance(reg_entity_child, RegisteredMetric):
            # should save parent's reg_entity_id
            reg_entity_child.reg_entity_id = reg_entity_parent.reg_entity_id
            #entity_obj = reg_entity_child.ref_entity
            #self.publish_unit(reg_entity_child, entity_obj.name, entity_obj.unit)
            return
        else:
            log.info("Registering parent and child relationship with IoTCV2 for {0} {1}".\
                     format(reg_entity_parent.ref_entity.name, reg_entity_child.ref_entity.name))
            # create relationship fun internal queue
            rel_resp_q = Queue.Queue()
            self.set_relationship = False

            def on_response(msg, rel_resp_q):
                try:
                    log.debug("Received msg: {0}".format(msg))
                    json_msg = json.loads(msg)
                    log.debug("Processed msg: {0}".format(json_msg["type"]))
                    if json_msg["type"] == "createRelationship_rsp" and json_msg["guid"] != "null" \
                        and json_msg["guid"] == reg_entity_parent.reg_entity_id:
                        log.info("Received createRelationship response")
                        if json_msg["result"] == 'SUCCESS':
                            self.set_relationship = True
                    else:
                        log.info("Waiting for create relationship response")
                        on_response(rel_resp_q.get(True, timeout), rel_resp_q)
                except:
                    raise Exception("Exception while create relationship")

            # create and add register request into req_list (waiting list)
            operation_id = self.next_id()
            req = Request(reg_entity_parent.reg_entity_id, operation_id, rel_resp_q)
            log.info("operation_id:{0} req:{1}".format(operation_id, req))
            with self.req_ops_lock:
                self.req_dict.update({str(operation_id): req})
                log.info("operation_id:{0} req_dict:{1}".format(operation_id, self.req_dict))
            self.comms.send(json.dumps(self._relationship(operation_id,
                            reg_entity_parent.reg_entity_id, reg_entity_child.reg_entity_id)))
            # block until there is an item available or timeout
            try:
                on_response(rel_resp_q.get(True, timeout), rel_resp_q)
            except:
                raise Exception("Exception while creating relationship")

            if not self.set_relationship:
                raise CreateRelationshipFailure()
            log.info("Relationship Created")

    def _format_data(self, reg_metric):
        met_cnt = reg_metric.values.qsize()
        if met_cnt == 0:
            return
        data = []
        for _ in range(met_cnt):
            m = reg_metric.values.get(block=True)
            if m is not None:
                data.append({"ts": m[0], "v": m[1]})
        if len(data) == 0:
            return

        metrics = []
        metrics_entry = {
            "metricName": reg_metric.ref_entity.name,
            "data": data
        }
        metrics.append(metrics_entry)

        # TBD: now, only 1 metric_data_entry, and for 1 MO
        metric_data = []
        metric_data_entry = {
            "MOguid": reg_metric.parent.ref_entity.entity_id,
            "metrics": metrics
        }
        metric_data.append(metric_data_entry)
        return json.dumps({
            "type": "putMetric_req",
            "metric_data": metric_data
        })

    def set_properties(self, reg_entity, properties):
        # RegisteredMetric get parent's guid; RegisteredEntity gets own guid

        if isinstance(reg_entity, RegisteredMetric):
            entity = reg_entity.parent.ref_entity
        else:
            entity = reg_entity.ref_entity

        log.info("Properties defined for resource {0}".format(entity.name))
        # set_properties fun internal queue
        set_prop_resp_q = Queue.Queue()
        self.set_prop = False

        def on_response(msg, set_prop_resp_q):
            try:
                log.debug("Received msg: {0}".format(msg))
                json_msg = json.loads(msg)
                log.debug("Processing msg: {0}".format(json_msg["type"]))
                if json_msg["type"] == "setProperties_rsp" and json_msg["guid"] != "null" and \
                                json_msg["guid"] == entity.entity_id:
                    log.info("Received set properties response for: {0}".format(json_msg["guid"]))
                    if json_msg["result"] == 'SUCCESS':
                        self.set_prop = True
                else:
                    log.info("Waiting for set properties response")
                    on_response(set_prop_resp_q.get(True, timeout), set_prop_resp_q)
            except:
                raise Exception("Exception while set properties")

        # create and add register request into req_list (waiting list)
        operation_id = self.next_id()
        req = Request(entity.entity_id, operation_id, set_prop_resp_q)
        log.info("operation_id:{0} req:{1}".format(operation_id, req))
        with self.req_ops_lock:
            self.req_dict.update({str(operation_id): req})
            log.info("operation_id:{0} req_dict:{1}".format(operation_id, self.req_dict))

        self.comms.send(json.dumps(
            self._properties(operation_id, entity.entity_type, entity.entity_id, entity.name, properties)))
        # block until there is an item available or timeout
        try:
            on_response(set_prop_resp_q.get(True, timeout), set_prop_resp_q)
        except:
            raise Exception("Exception while setting properties")

        if not self.set_prop:
            raise SetPropertiesFailure()
        log.info("Set Properties for {0} succeeded".format(entity.name))

    def unregister(self, entity_obj):
        pass

    def _registration(self, operation_id, guid, mo_name, mo_type):
        log.info("operation_id:{0} guid:{1}".format(operation_id, guid))
        return {
            "type": "registerMO_req",
            "guid" : guid,
            "name" : mo_name,
            "MOType" : mo_type,
            "operation_id" : operation_id
        }

    def _properties(self, operation_id, mo_type, guid, mo_name, properties):
        msg = {
            "type": "setProperties_req",
            "guid" : guid,
            "name" : mo_name,
            "MOType" : mo_type,
            "operation_id" : operation_id,
            "properties": []
        }
        for key, value in properties.items():
            msg["properties"].append({"key": key, "value": value})
        return msg

    def _relationship(self, operation_id, parent_res_uuid, child_res_uuid):
        return {
            "type": "createRelationships_req",
            "operation_id" : operation_id,
            "parent": parent_res_uuid,
            "child": child_res_uuid
        }

    def next_id(self):
        self.counter = (self.counter + 1) & 0xffffff
        # Enforce even IDs
        return int(self.counter * 2)

    def _dispatch_recvd_msg(self):
        log.info("Dispatching received messages from IoTCV2")

        while True:
            try:
                # block until there is an item available
                msg = self.recv_msg_queue.get(True)
                log.debug("Received msg: {0}".format(msg))
                json_msg = json.loads(msg)
                log.debug("Processing msg: type:{0} operation_id:{1}".format(json_msg["type"], json_msg["operation_id"]))
                # search matched request in request dictionary
                # assume operation_id will be unique in one process
                log.debug("self.req_dict {0} keys:{1}".format(self.req_dict, self.req_dict.keys()))
                if (json_msg["operation_id"] in self.req_dict.keys()):
                    req = self.req_dict[json_msg["operation_id"]]
                    log.debug("self.req_dict {0} req:{1}".format(self.req_dict, req))
                    # get/delete request from dictionary
                    if (req is not None):
                        log.debug("json_msg['guid'] {0} req.guid:{1}".format(json_msg["guid"], req.guid))
                        # double confirm guid
                        if (json_msg["guid"] != req.guid):
                            continue
                        with self.req_ops_lock:
                            del self.req_dict[json_msg["operation_id"]]
                        # put response into requester's reception queue
                        log.debug("self.req_dict {0} msg:{1} user_queue{2}".format(self.req_dict, msg, req.user_queue))
                        req.user_queue.put(msg)
                else:
                    # TBD: it may be other messages, e.g., Action Request, need to process
                    log.info("received unexpected messages")
            except Exception as er:
                log.exception("Exception in dispatching received messages: %s" % str(er))