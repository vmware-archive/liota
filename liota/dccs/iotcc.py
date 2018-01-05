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
import sys
import logging
import time
import threading
import ConfigParser
import os
import Queue
import datetime
from time import gmtime, strftime
from threading import Lock
import ast
from re import match

from liota.dccs.dcc import DataCenterComponent, RegistrationFailure
from liota.entities.metrics.metric import Metric
from liota.lib.utilities.utility import LiotaConfigPath, getUTCmillis, mkdir, read_liota_config
from liota.lib.utilities.si_unit import parse_unit
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.entities.registered_entity import RegisteredEntity

log = logging.getLogger(__name__)
timeout = int(read_liota_config('IOTCC_PATH', 'iotcc_response_timeout'))


class Request:
    def __init__(self, transaction_id, user_queue):
        # assume transaction_id will be unique in one process
        self.transaction_id = transaction_id
        self.user_queue = user_queue


class IotControlCenter(DataCenterComponent):
    """ The implementation of IoTCC cloud provider solution

    """

    def __init__(self, con):
        """
        Initialization of IoT Pulse Center

        :param con: DCC Comms connection Object
        """
        log.info("Logging into DCC")
        self._dcc_load_time = datetime.datetime.now()
        self._version = 20171118
        self.comms = con
        if not self.comms.identity.username:
            log.error("Username not found")
            raise ValueError("Username not found")
        elif not self.comms.identity.password:
            log.error("Password not found")
            raise ValueError("Password not found")
        recv_thread = threading.Thread(target=self.comms.receive)
        recv_thread.daemon = True
        # This thread will continuously run in background to receive response or actions from DCC
        recv_thread.start()
        # Wait for Subscription to be complete and then proceed to publish message
        time.sleep(0.5)
        self._iotcc_json = self._create_iotcc_json()
        self._iotcc_json_load_retry = int(read_liota_config('IOTCC_PATH', 'iotcc_load_retry'))
        self.enable_reboot_getprop = read_liota_config('IOTCC_PATH', 'enable_reboot_getprop')
        self._sys_properties = read_liota_config('IOTCC_PATH', 'system_properties')
        self.counter = 0
        self._recv_msg_queue = self.comms.userdata
        self._req_ops_lock = Lock()
        self._req_dict = {}
        dispatch_thread = threading.Thread(target=self._dispatch_recvd_msg)
        dispatch_thread.daemon = True
        # This thread will continuously run in background to check and dispatch received responses
        dispatch_thread.start()
        self.dev_file_path = self._get_file_storage_path("dev_file_path")
        # Liota internal entity file system path special for iotcc
        self.entity_file_path = self._get_file_storage_path("entity_file_path")
        self.file_ops_lock = Lock()

    def register(self, entity_obj):
        """
        Register the entity Object to IoT Pulse DCC,
        metric is not registered so simply return the RegisteredMetric object
        :param entity_obj: Metric or Entity Object
        :return: RegisteredMetric or RegisteredEntity Object
        """
        self._assert_input(entity_obj.name, 50)
        self._assert_input(entity_obj.entity_type, 50)

        if isinstance(entity_obj, Metric):
            # reg_entity_id should be parent's one: not known here yet
            # will add in creat_relationship(); publish_unit should be done inside
            return RegisteredMetric(entity_obj, self, None)
        else:
            # finally will create a RegisteredEntity
            log.info("Registering resource with IoTCC {0}".format(entity_obj.name))
            reg_resp_q = Queue.Queue()

            def on_response(msg, reg_resp_q):
                log.debug("Received msg: {0}".format(msg))
                json_msg = json.loads(msg)
                log.debug("Processing msg: {0}".format(json_msg["type"]))
                self._check_version(json_msg)
                if json_msg["type"] == "create_or_find_resource_response" and json_msg["body"]["uuid"] != "null" and \
                                json_msg["body"]["id"] == entity_obj.entity_id:
                    log.info("FOUND RESOURCE: {0}".format(json_msg["body"]["uuid"]))
                    self.reg_entity_id = json_msg["body"]["uuid"]
                else:
                    log.info("Waiting for resource creation")
                    on_response(reg_resp_q.get(True, timeout), reg_resp_q)

            if entity_obj.entity_type == "EdgeSystem":
                entity_obj.entity_type = "HelixGateway"
            transaction_id = self._next_id()
            req = Request(transaction_id, reg_resp_q)
            log.debug("Updating resource registration queue for transaction_id:{0}".format(transaction_id))
            with self._req_ops_lock:
                self._req_dict.update({transaction_id: req})
            self.comms.send(json.dumps(
                self._registration(transaction_id, entity_obj.entity_id, entity_obj.name, entity_obj.entity_type)))
            on_response(reg_resp_q.get(True, timeout), reg_resp_q)
            if not self.reg_entity_id:
                raise RegistrationFailure()
            log.info("Resource Registered {0}".format(entity_obj.name))
            if entity_obj.entity_type == "HelixGateway":
                with self.file_ops_lock:
                    self._store_reg_entity_details(entity_obj.entity_type, entity_obj.name, self.reg_entity_id,
                                                   entity_obj.entity_id)
                    self._store_reg_entity_attributes("EdgeSystem", entity_obj,
                                                      self.reg_entity_id, None, None)
            else:
                # get dev_type, and prop_dict if possible
                with self.file_ops_lock:
                    self._store_reg_entity_attributes("Devices", entity_obj, self.reg_entity_id,
                                                      entity_obj.entity_type, None)

            _reg_entity_obj = RegisteredEntity(entity_obj, self, self.reg_entity_id)
            if self._sys_properties:
                _sys_prop_dict = ast.literal_eval(self._sys_properties)
                if isinstance(_sys_prop_dict, dict) and _sys_prop_dict:
                    self.set_properties(_reg_entity_obj, _sys_prop_dict)
                    log.info(
                        "System Properties {0} defined for the resource {1}".format(self._sys_properties,
                                                                                    entity_obj.name))
                else:
                    log.info("System Properties {0} not defined for the resource {1}".format(self._sys_properties,
                                                                                             entity_obj.name))
            return _reg_entity_obj

    def _check_version(self, json_msg):
        if json_msg["version"] != self._version:
            raise Exception(
                "CLIENT SERVER VERSION MISMATCH. CLIENT VERSION IS: {0}. SERVER VERSION IS: {1}".format(self._version,
                                                                                                        json_msg[
                                                                                                            "version"]))

    def unregister(self, entity_obj):
        """
        Unregister the Entity Object
        :param entity_obj: Registered Entity
        :return:
        """

        log.info("Unregistering resource with IoTCC {0}".format(entity_obj.ref_entity.name))
        unreg_resp_q = Queue.Queue()
        transaction_id = self._next_id()
        req = Request(transaction_id, unreg_resp_q)
        log.debug("Updating unregister response queue for transaction_id:{0}".format(transaction_id))
        with self._req_ops_lock:
            self._req_dict.update({transaction_id: req})
        self.comms.send(json.dumps(self._unregistration(transaction_id, entity_obj.ref_entity)))
        response = self._handle_response(unreg_resp_q.get(True, timeout))
        if response:
            log.info("Unregistration of resource {0} with IoTCC succeeded".format(entity_obj.ref_entity.name))
            if entity_obj.ref_entity.entity_type != "HelixGateway":
                self._store_device_info(entity_obj.reg_entity_id, entity_obj.ref_entity.name,
                                        entity_obj.ref_entity.entity_type, None, True)
            else:
                self._remove_reg_entity_details(entity_obj.ref_entity.name, entity_obj.reg_entity_id)
                self._store_device_info(entity_obj.reg_entity_id, entity_obj.ref_entity.name, None, None, True)
        else:
            raise Exception("Unregistration of resource {0} unsuccessful with IoTCC".format(entity_obj.ref_entity.name))

    def create_relationship(self, reg_entity_parent, reg_entity_child):
        """
        This method creates Parent-Child relationship.  Supported relationships are:

                EdgeSystem
                    |                                      EdgeSystem
                 Device                   (or)                |
                    |                                    RegisteredMetric
              RegisteredMetric

        However, A single EdgeSystem can have multiple child Devices and a each Device can have
        multiple child Metrics.

        :param reg_entity_parent: Registered EdgeSystem or Registered Device Object
        :param reg_entity_child:  Registered Device or Registered Metric Object
        :return: None
         """
        # sanity check: must be RegisteredEntity or RegisteredMetricRegisteredMetric
        if (not isinstance(reg_entity_parent, RegisteredEntity)) \
                or (not isinstance(reg_entity_child, RegisteredEntity) \
                            and not isinstance(reg_entity_child, RegisteredMetric)):
            raise TypeError()

        reg_entity_child.parent = reg_entity_parent
        if isinstance(reg_entity_child, RegisteredMetric):
            # should save parent's reg_entity_id
            reg_entity_child.reg_entity_id = reg_entity_parent.reg_entity_id
            entity_obj = reg_entity_child.ref_entity
            # If the units are passed from user code they`ll be set as unit properties
            if entity_obj.unit is not None:
                self.publish_unit(reg_entity_child, entity_obj.name, entity_obj.unit)
        else:
            # create relationship internal queue
            rel_resp_q = Queue.Queue()
            transaction_id = self._next_id()
            req = Request(transaction_id, rel_resp_q)
            log.debug("Updating create relationship response queue for transaction_id:{0}".format(transaction_id))
            with self._req_ops_lock:
                self._req_dict.update({transaction_id: req})
            self.comms.send(json.dumps(self._relationship(transaction_id,
                                                          reg_entity_parent.ref_entity,
                                                          reg_entity_child.ref_entity)))
            response = self._handle_response(rel_resp_q.get(True, timeout))
            if response:
                log.info("Relationship between entities {0} & {1} created successfully in IoTCC".format(
                    reg_entity_parent.ref_entity.name, reg_entity_child.ref_entity.name))
            else:
                raise Exception("Relationship creation between entities {0} & {1} failed in IoTCC".format(
                    reg_entity_parent.ref_entity.name, reg_entity_child.ref_entity.name))

    def _handle_response(self, msg):
        """
        Process the responses for various types of request messages
        :param msg: response message received
        :return: boolean
        """
        log.debug("Received msg: {0}".format(msg))
        json_msg = json.loads(msg)
        log.debug("Processing msg: {0}".format(json_msg["type"]))
        self._check_version(json_msg)
        return json_msg["body"]["result"] == "succeeded"

    def _registration(self, msg_id, res_id, res_name, res_kind):
        return {
            "transactionID": msg_id,
            "version": self._version,
            "type": "create_or_find_resource_request",
            "body": {
                "kind": res_kind,
                "id": res_id,
                "name": res_name
            }
        }

    def _relationship(self, msg_id, parent_entity, child_entity):
        return {
            "transactionID": msg_id,
            "version": self._version,
            "type": "create_relationship_request",
            "body": {
                "parent": {
                    "kind": parent_entity.entity_type,
                    "id": parent_entity.entity_id,
                    "name": parent_entity.name
                },
                "child": {
                    "kind": child_entity.entity_type,
                    "id": child_entity.entity_id,
                    "name": child_entity.name
                }
            }
        }

    def _properties(self, msg_id, entity_type, entity_id, entity_name, timestamp, properties):
        msg = {
            "transactionID": msg_id,
            "version": self._version,
            "type": "add_properties_request",
            "body": {
                "kind": entity_type,
                "id": entity_id,
                "name": entity_name,
                "timestamp": timestamp,
                "property_data": []
            }
        }
        for key, value in properties.items():
            self._assert_input(key, 100)
            self._assert_input(value, 255)
            msg["body"]["property_data"].append({"propertyKey": key, "propertyValue": value})
        return msg

    def _get_properties(self, msg_id, ref_entity):
        return {
            "transactionID": msg_id,
            "version": self._version,
            "type": "get_properties_request",
            "body": {
                "kind": ref_entity.entity_type,
                "id": ref_entity.entity_id,
                "name": ref_entity.name
            }
        }

    def _format_data(self, reg_metric):
        met_cnt = reg_metric.values.qsize()
        if met_cnt == 0:
            return
        _timestamps = []
        _values = []
        for _ in range(met_cnt):
            m = reg_metric.values.get(block=True)
            if m is not None:
                _timestamps.append(m[0])
                _values.append(m[1])
        if _timestamps == []:
            return
        return json.dumps({
            "type": "add_stats",
            "version": self._version,
            "body": {
                "kind": reg_metric.parent.ref_entity.entity_type,
                "id": reg_metric.parent.ref_entity.entity_id,
                "name": reg_metric.parent.ref_entity.name,
                "metric_data": [{
                    "statKey": reg_metric.ref_entity.name,
                    "timestamps": _timestamps,
                    "data": _values
                }]

            }
        })

    def set_properties(self, reg_entity_obj, properties):
        """
        Set Properties for Registered Entity (Edge System or Devices)
        :param reg_entity_obj: RegisteredEntity Object
        :param properties: Properties List
        :return:
        """
        # RegisteredMetric get parent's resid; RegisteredEntity gets own resid
        reg_entity_id = reg_entity_obj.reg_entity_id

        if isinstance(reg_entity_obj, RegisteredMetric):
            entity = reg_entity_obj.parent.ref_entity
        else:
            entity = reg_entity_obj.ref_entity

        set_prop_resp_q = Queue.Queue()
        # create and add register request into req_list (waiting list)
        transaction_id = self._next_id()
        req = Request(transaction_id, set_prop_resp_q)
        log.debug("Updating set properties response queue for transaction_id:{0}".format(transaction_id))
        with self._req_ops_lock:
            self._req_dict.update({transaction_id: req})
        self.comms.send(json.dumps(
            self._properties(transaction_id, entity.entity_type, entity.entity_id, entity.name,
                             getUTCmillis(), properties)))
        response = self._handle_response(set_prop_resp_q.get(True, timeout))
        if response:
            log.info("Properties defined for resource {0}".format(entity.name))
        else:
            raise Exception("Setting Properties for resource {0} failed".format(entity.name))
        if entity.entity_type == "HelixGateway":
            with self.file_ops_lock:
                self._store_reg_entity_attributes("EdgeSystem", entity,
                                                  reg_entity_obj.reg_entity_id, None, properties)
        else:
            # get dev_type, and prop_dict if possible
            with self.file_ops_lock:
                self._store_reg_entity_attributes("Devices", entity, reg_entity_obj.reg_entity_id,
                                                  entity.entity_type, properties)

    def publish_unit(self, reg_entity_obj, metric_name, unit):
        """
         Publish SI units as properties for Metrics but RegisteredMetric object are simply returned
         so currently units are set to the parent RegisteredEntity(Device or EdgeSystem)
         Either units are set with prefix as properties or only unit gets set as property if prefix doesn't exist.
        :param reg_entity_obj: RegisteredEntity Object
        :param metric_name: Metric Name
        :param unit: SI Unit
        :return:
        """
        str_prefix, str_unit_name = parse_unit(unit)
        if not isinstance(str_prefix, basestring) and isinstance(str_unit_name, basestring):
            properties_unit_dict = {
                metric_name + "_unit": str_unit_name
            }
            log.debug("Publishing unit {0} for metric {1} to IoTCC for resource {2}".format(str_unit_name, metric_name,
                                                                                            reg_entity_obj.parent.ref_entity.name))
        elif isinstance(str_unit_name, basestring) and isinstance(str_prefix, basestring):
            properties_unit_dict = {
                metric_name + "_unit": str_unit_name,
                metric_name + "_prefix": str_prefix
            }
            log.debug(
                "Publishing unit {0} with prefix {1} for metric {2} to IoTCC for resource {3}".format(str_unit_name,
                                                                                                      str_prefix,
                                                                                                      metric_name,
                                                                                                      reg_entity_obj.parent.ref_entity.name))
        else:
            properties_unit_dict = {}
            log.debug("{0} metric unit with prefix cannot be parsed and published to IoTCC for resource {1}".format(
                metric_name, reg_entity_obj.parent.ref_entity.name))
        if properties_unit_dict:
            self.set_properties(reg_entity_obj, properties_unit_dict)
            log.info("Published units for metric {0} to IoTCC for resource {1}".format(metric_name,
                                                                                       reg_entity_obj.parent.ref_entity.name))

    def _create_iotcc_json(self):
        msg = {
            "iotcc": {
                "EdgeSystem": {"SystemName": "", "EntityType": "", "uuid": "", "LocalUuid": ""},
                "OGProperties": {"OrganizationGroup": ""},
                "Devices": []
            }
        }

        iotcc_path = read_liota_config('IOTCC_PATH', 'iotcc_path')
        path = os.path.dirname(iotcc_path)
        mkdir(path)
        try:
            with open(iotcc_path, 'w') as f:
                json.dump(msg, f, sort_keys=True, indent=4, ensure_ascii=False)
                log.debug('Initialized ' + iotcc_path)
            f.close()
        except IOError, err:
            log.error('Could not open {0} file '.format(iotcc_path) + err)
        return iotcc_path

    def _store_reg_entity_details(self, entity_type, entity_name, reg_entity_id, entity_local_uuid):
        if self._iotcc_json == '':
            log.warn('iotcc.json file missing')
            return
        try:
            f = open(self._iotcc_json, 'r')
        except IOError, err:
            log.exception('Could not open {0} file '.format(self._iotcc_json) + str(err))
            return

        def load_json_record(f):
            record = ''
            try:
                record = json.load(f)
            except:
                log.exception('Could not load json record from {0} '.format(self._iotcc_json))
            return record

        local_cnt = 1
        msg = load_json_record(f)
        while ((msg == '') and (local_cnt <= self._iotcc_json_load_retry)):
            local_cnt += 1
            msg = load_json_record(f)
        f.close()
        if msg == '':
            log.error('Tried {0} times, while failed to load record from {0}'.format(local_cnt, self._iotcc_json))
            return

        log.debug('{0}:{1}'.format(entity_name, reg_entity_id))
        if entity_type == "HelixGateway":
            msg["iotcc"]["EdgeSystem"]["SystemName"] = entity_name
            msg["iotcc"]["EdgeSystem"]["uuid"] = reg_entity_id
            msg["iotcc"]["EdgeSystem"]["EntityType"] = entity_type
            msg["iotcc"]["EdgeSystem"]["LocalUuid"] = entity_local_uuid
        else:
            entity_exist = False
            for device in msg["iotcc"]["Devices"]:
                if device["uuid"] == reg_entity_id and device["EntityType"] == entity_type and device[
                    "uuid"] == reg_entity_id:
                    entity_exist = True
                    break
            if not entity_exist:
                msg["iotcc"]["Devices"].append(
                    {"DeviceName": entity_name, "uuid": reg_entity_id, "EntityType": entity_type,
                     "LocalUuid": entity_local_uuid})
        if msg != '':
            with open(self._iotcc_json, 'w') as f:
                json.dump(msg, f, sort_keys=True, indent=4, ensure_ascii=False)
            f.close()

    def _remove_reg_entity_details(self, entity_name, reg_entity_id):
        if self._iotcc_json == '':
            log.warn('iotcc.json file missing')
            return
        try:
            with open(self._iotcc_json, 'r') as f:
                msg = json.load(f)
            f.close()
        except IOError, err:
            log.error('Could not open {0} file '.format(self._iotcc_json) + str(err))
        log.debug('Remove {0}:{1} from iotcc.json'.format(entity_name, reg_entity_id))
        if msg["iotcc"]["EdgeSystem"]["SystemName"] == entity_name and msg["iotcc"]["EdgeSystem"][
            "uuid"] == reg_entity_id:
            del msg["iotcc"]["EdgeSystem"]
            log.info("Removed {0} edge-system from iotcc.json".format(entity_name))
        else:
            entity_exist = False
            for device in msg["iotcc"]["Devices"]:
                if device["uuid"] == reg_entity_id and device["uuid"] == reg_entity_id:
                    entity_exist = True
                    try:
                        msg["iotcc"]["Devices"].remove(device)
                        log.info("Device {0} removed from iotcc.json".format(entity_name))
                        break
                    except ValueError:
                        pass
            if not entity_exist:
                log.error("No such device {0} exists".format(entity_name))
        with open(self._iotcc_json, 'w') as f:
            json.dump(msg, f, sort_keys=True, indent=4, ensure_ascii=False)
        f.close()

    def _write_entity_json_file(self, prop_dict, attribute_list, uuid, remove):
        if prop_dict is not None:
            for key in prop_dict.iterkeys():
                value = prop_dict[key]
                if key == 'entity type' or key == 'name' or key == 'device type' or key == 'Entity_Timestamp':
                    continue
                attribute_list.append({key: value})
        attribute_list.append({"LastSeenTimestamp": strftime("%Y-%m-%dT%H:%M:%S", gmtime())})
        log.debug('attribute_list: {0}'.format(attribute_list))
        msg = {
            "discovery": {
                "remove": remove,
                "attributes": attribute_list
            }
        }
        log.debug('msg: {0}'.format(msg))
        log.debug("store_entity_json_file dev_file_path:{0}".format(self.dev_file_path))
        file_path = self.dev_file_path + '/' + uuid + '.json'
        try:
            with open(file_path, 'w') as f:
                json.dump(msg, f, sort_keys=True, indent=4, ensure_ascii=False)
                log.debug('Initialized ' + file_path)
            f.close()
        except IOError, err:
            log.error('Could not open {0} file '.format(file_path) + err)

    def _store_edge_system_info(self, uuid, name, prop_dict, remove):
        """
        create (can overwrite) edge system info file of UUID.json, with format of
        {
            "discovery":  {
                "remove": false,
                "attributes": [
                    {"edge system name" : "EdgeSystem-Name"},
                    {"attribute name" : "attribute value"},
                    …
                ]
            }
        }
        except the first attribute is edge system name, all other attributes may vary
        """

        log.debug("store_edge_system_info")
        log.debug('{0}:{1}, prop_list: {2}'.format(uuid, name, prop_dict))
        attribute_list = [{"edge system name": name}]
        self._write_entity_json_file(prop_dict, attribute_list, uuid, remove)

    def _store_device_info(self, uuid, name, dev_type, prop_dict, remove_device):
        """
        create (can overwrite) device info file of device_UUID.json, with format of
        {
            "discovery":  {
                "remove": false,
                "attributes": [
                    {"IoTDeviceType" : "LM35"},
                    {"IoTDeviceName" : "LM35-12345"},
                    {"model": "LM35-A2"},
                    {"function": "thermistor"},
                    {"port" : "GPIO-3"},
                    {"manufacturer" : "Texas Instrument"},
                    {"LastSeenTimestamp" : "04 NOV 2016"}
                ]
            }
        }
        except IoTDeviceType and IoTDeviceName, all other attributes may vary
        """
        log.debug("store_device_info")
        log.debug('prop_dict: {0}'.format(prop_dict))
        attribute_list = [{"IoTDeviceType": dev_type},
                          {"IoTDeviceName": name}]
        self._write_entity_json_file(prop_dict, attribute_list, uuid, remove_device)

    def _write_entity_file(self, prop_dict, res_uuid):
        file_path = self.entity_file_path + '/' + res_uuid + '.json'
        prop_dict.update({"Entity_Timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")})
        try:
            with open(file_path, "w") as json_file:
                if (prop_dict is not None):
                    json_string = json.dumps(prop_dict)
                    json_file.write(json_string)
        except:
            log.error('Write file error')

    def _read_entity_file(self, res_uuid):
        file_path = self.entity_file_path + '/' + res_uuid + '.json'
        prop_dict = None
        try:
            with open(file_path, "r") as json_file:
                prop_dict = json.loads(json_file.read())
        except:
            log.error('Read file error')
        return prop_dict

    def _merge_prop_dict_list(self, prop_dict, prop_list):
        # prop_dict: new property dictionary
        # prop_list: list of dictionary items
        if (prop_list is None):
            return prop_dict
        if (prop_dict is None):
            prop_dict = {}
        for item in prop_list:
            prop_dict.update(item)
        # get updated dict
        return prop_dict

    def _store_reg_entity_attributes(self, entity_type, entity, reg_entity_id,
                                     dev_type, prop_dict):
        entity_name = entity.name
        log.debug('store_reg_entity_attributes {0}:{1}:{2}:{3}'.format(entity_type,
                                                                       entity_name, reg_entity_id, prop_dict))

        ### Update IOTCC local entity file first
        # look for uuid.json file first, if not, first time to write
        # name + type (edge system or device) + if device, device type, + prop_dict
        # if file exists, check name, type and device type match or not
        # if match, merge prop_dict to that file (with existing properties)
        # if not match, replace with new above info + only prop_dict
        # (old property will not be used since outdated already)
        file_path = self.entity_file_path + '/' + reg_entity_id + '.json'
        if not os.path.exists(file_path):
            tmp_dict = {'entity type': str(entity_type), 'name': str(entity_name)}
            if (dev_type is not None):
                tmp_dict.update({"device type": str(dev_type)})
            else:
                tmp_dict.update({"device type": ""})
            if (tmp_dict is not None) and (prop_dict is not None):
                new_prop_dict = dict(tmp_dict.items() + prop_dict.items())
            else:
                new_prop_dict = tmp_dict
        else:
            tmp_dict = self._read_entity_file(reg_entity_id)
            # check Entity_Timestamp of entity_file: if < _dcc_load_time, get properties from cloud
            if (self.enable_reboot_getprop == "True") and ('Entity_Timestamp' in tmp_dict):
                last_dtime = datetime.datetime.strptime(tmp_dict["Entity_Timestamp"], "%Y-%m-%dT%H:%M:%S")
                if (last_dtime <= self._dcc_load_time):
                    list_prop = self.get_properties(entity)
                    # merge property info from get_properties() into our local entity record
                    tmp_dict = self._merge_prop_dict_list(tmp_dict, list_prop)
            if ((('entity type' in tmp_dict) and (tmp_dict["entity type"] == entity_type)) and
                    (('name' in tmp_dict) and (tmp_dict["name"] == entity_name)) and
                    (('device type' in tmp_dict) and ((tmp_dict["device type"] == dev_type) or
                                                          ((tmp_dict["device type"] == '') and (dev_type == None))))):
                # the same entity
                if (tmp_dict is not None) and (prop_dict is not None):
                    new_prop_dict = dict(tmp_dict.items() + prop_dict.items())
                else:
                    new_prop_dict = tmp_dict
            else:
                tmp_dict = {'entity type': str(entity_type), 'name': str(entity_name)}
                if (dev_type is not None):
                    tmp_dict.update({"device type": str(dev_type)})
                else:
                    tmp_dict.update({"device type": ""})
                if (tmp_dict is not None) and (prop_dict is not None):
                    new_prop_dict = dict(tmp_dict.items() + prop_dict.items())
                else:
                    new_prop_dict = tmp_dict

        # write new property dictionary to local entity file
        self._write_entity_file(new_prop_dict, reg_entity_id)
        ### Write IOTCC device file for AW agents
        if entity_type == "EdgeSystem":
            self._store_edge_system_info(reg_entity_id, entity_name, new_prop_dict, False)
        elif entity_type == "Devices":
            self._store_device_info(reg_entity_id, entity_name, dev_type, new_prop_dict, False)
        else:
            return

    def _get_file_storage_path(self, name):
        config = ConfigParser.RawConfigParser()
        fullPath = LiotaConfigPath().get_liota_fullpath()
        if fullPath != '':
            try:
                if config.read(fullPath) != []:
                    try:
                        # retrieve device info file storage directory
                        file_path = config.get('IOTCC_PATH', name)
                        log.debug("_get_{0} file_path:{1}".format(name, file_path))
                    except ConfigParser.ParsingError as err:
                        log.error('Could not open config file ' + err)
                        return None
                    if not os.path.exists(file_path):
                        try:
                            os.makedirs(file_path)
                        except OSError as exc:  # Python >2.5
                            if exc.errno == errno.EEXIST and os.path.isdir(file_path):
                                pass
                            else:
                                log.error('Could not create file storage directory')
                                return None
                    return file_path
                else:
                    log.error('Could not open config file ' + fullPath)
                    return None
            except IOError, err:
                log.error('Could not open config file')
                return None
        else:
            # missing config file
            log.warn('liota.conf file missing')
            return None

    def _next_id(self):
        self.counter = (self.counter + 1) & 0xffffff
        # Enforce even IDs
        return int(self.counter * 2)

    def _unregistration(self, msg_id, ref_entity):
        return {
            "transactionID": msg_id,
            "version": self._version,
            "type": "remove_resource_request",
            "body": {
                "kind": ref_entity.entity_type,
                "id": ref_entity.entity_id,
                "name": ref_entity.name
            }
        }

    def get_properties(self, entity):
        """
        Get the list of properties from IoT Pulse DCC

        :param resource_uuid: Resource Unique Identifier
        :return:
        """
        log.info("Get properties defined with IoTCC for resource {0}".format(entity.entity_id))
        self.prop_list = None
        get_prop_resp_q = Queue.Queue()

        def on_response(msg, get_prop_resp_q):
            try:
                log.debug("Received msg: {0}".format(msg))
                json_msg = json.loads(msg)
                log.debug("Processing msg: {0}".format(json_msg["type"]))
                self._check_version(json_msg)
                if json_msg["type"] == "get_properties_response" and json_msg["body"]["id"] != "null" and \
                                json_msg["body"]["id"] == entity.entity_id:
                    log.info("FOUND PROPERTY LIST: {0}".format(json_msg["body"]["propertyList"]))
                    self.prop_list = json_msg["body"]["propertyList"]
                else:
                    log.info("Waiting for getting properties")
                    on_response(self.get_prop_resp_q.get(True, timeout), get_prop_resp_q)
            except:
                log.exception("Exception while getting properties")

        transaction_id = self._next_id()
        req = Request(transaction_id, get_prop_resp_q)
        log.debug("Updating get properties response queue for transaction_id:{0}".format(transaction_id))
        with self._req_ops_lock:
            self._req_dict.update({transaction_id: req})
        self.comms.send(json.dumps(self._get_properties(transaction_id, entity)))
        on_response(get_prop_resp_q.get(True, timeout), get_prop_resp_q)
        return self.prop_list

    def _assert_input(self, input, max_length):
        """ validates if the input string contains only the whitelisted characters """
        if not match('^[A-Za-z0-9\s\._-]+$', input):
            raise ValueError("The provided string contains unacceptable character : {0}".format(input))
        if not len(input) <= max_length:
            raise ValueError("The provided string contains more than {0} characters : {1}".format(max_length, input))

    def _dispatch_recvd_msg(self):
        log.debug("Dispatching received messages from IOTCC")

        while True:
            try:
                # block until there is an item available
                msg = self._recv_msg_queue.get(True)
                log.debug("Received msg: {0}".format(msg))
                json_msg = json.loads(msg)
                log.debug(
                    "Processing msg: type:{0} transaction_id:{1}".format(json_msg["type"], json_msg["transactionID"]))
                # search matched request in request dictionary
                # assume transaction_id will be unique in one process
                log.debug("Dictionary keys:{0}".format(self._req_dict.keys()))
                req = self._req_dict.get(json_msg["transactionID"])
                # get/delete request from dictionary
                if (req is not None):
                    with self._req_ops_lock:
                        del self._req_dict[json_msg["transactionID"]]
                    # put response into requester's reception queue
                    log.debug("Msg:{0} dispatched to user queue".format(msg))
                    req.user_queue.put(msg)
                else:
                    # TBD: it may be other messages, e.g., Actions, Armada Campaign
                    log.warn("Received unexpected message {0}".format(msg))
            except Exception:
                log.exception("Exception in dispatching the received messages")
