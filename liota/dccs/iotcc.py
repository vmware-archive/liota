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
import ConfigParser
import os
import Queue
from time import gmtime, strftime
from threading import Lock
import xml.etree.cElementTree as ET
from xml.dom import minidom

from liota.dccs.dcc import DataCenterComponent, RegistrationFailure
from liota.lib.protocols.helix_protocol import HelixProtocol
from liota.entities.metrics.metric import Metric
from liota.lib.utilities.utility import LiotaConfigPath, getUTCmillis, mkdir, read_liota_config, store_edge_system_uuid
from liota.lib.utilities.si_unit import parse_unit
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.entities.registered_entity import RegisteredEntity

log = logging.getLogger(__name__)


class IotControlCenter(DataCenterComponent):
    """ The implementation of IoTCC cloud provider solution

    """

    def __init__(self, username, password, con):
        log.info("Logging into DCC")
        self.comms = con
        self.username = username
        self.password = password
        thread = threading.Thread(target=self.comms.receive)
        thread.daemon = True
        # This thread will continuously run in background to receive response or actions from DCC
        thread.start()
        self.proto = HelixProtocol(self.comms, username, password)
        self._iotcc_json = self._create_iotcc_json()
        self.counter = 0
        self.recv_msg_queue = self.comms.userdata
        self.dev_file_path = self._get_file_storage_path("dev_file_path")
        # Liota internal entity file system path special for iotcc
        self.entity_file_path = self._get_file_storage_path("entity_file_path")
        self.file_ops_lock = Lock()

        def on_response(msg):
            try:
                log.debug("Received msg: {0}".format(msg))
                json_msg = json.loads(msg)
                self.proto.on_receive(json_msg)
                if json_msg["type"] == "connection_response" and json_msg["body"]["result"] == "succeeded":
                    log.info("Connection verified")
                    return True
                else:
                    log.debug("Processed msg: {0}".format(json_msg["type"]))
                    on_response(self.recv_msg_queue.get(True,300))
            except Exception as error:
                log.error("HelixProtocolException: " + repr(error))

        # Block on Queue for not more then 300 seconds else it will raise an exception
        on_response(self.recv_msg_queue.get(True,300))
        log.info("Logged in to DCC successfully")

    def register(self, entity_obj):
        """ Register the objects

        """
        if isinstance(entity_obj, Metric):
            # reg_entity_id should be parent's one: not known here yet
            # will add in creat_relationship(); publish_unit should be done inside
            return RegisteredMetric(entity_obj, self, None)
        else:
            # finally will create a RegisteredEntity
            log.info("Registering resource with IoTCC {0}".format(entity_obj.name))

            def on_response(msg):
                try:
                    log.debug("Received msg: {0}".format(msg))
                    json_msg = json.loads(msg)
                    log.debug("Processed msg: {0}".format(json_msg["type"]))
                    if json_msg["type"] == "create_or_find_resource_response" and json_msg["body"]["uuid"] != "null" and \
                                    json_msg["body"]["id"] == entity_obj.entity_id:
                        log.info("FOUND RESOURCE: {0}".format(json_msg["body"]["uuid"]))
                        self.reg_entity_id = json_msg["body"]["uuid"]
                    else:
                        log.info("Waiting for resource creation")
                        on_response(self.recv_msg_queue.get(True,300))
                except:
                    raise Exception("Exception while registering resource")

            if entity_obj.entity_type == "EdgeSystem":
                entity_obj.entity_type = "HelixGateway"
            self.comms.send(json.dumps(
                self._registration(self.next_id(), entity_obj.entity_id, entity_obj.name, entity_obj.entity_type)))
            on_response(self.recv_msg_queue.get(True,300))
            if not self.reg_entity_id:
                raise RegistrationFailure()
            log.info("Resource Registered {0}".format(entity_obj.name))
            if entity_obj.entity_type == "HelixGateway":
                self.store_reg_entity_details(entity_obj.entity_type, entity_obj.name, self.reg_entity_id)
                store_edge_system_uuid(entity_name=entity_obj.name, entity_id=entity_obj.entity_id,
                                       reg_entity_id=self.reg_entity_id)
                with self.file_ops_lock:
                    self.store_reg_entity_attributes("EdgeSystem", entity_obj.name,
                                                     self.reg_entity_id, None, None)
            else:
                self.store_reg_entity_details(entity_obj.entity_type, entity_obj.name, self.reg_entity_id)
                # get dev_type, and prop_dict if possible
                with self.file_ops_lock:
                    self.store_reg_entity_attributes("Devices", entity_obj.name, self.reg_entity_id,
                                                     entity_obj.entity_type, None)

            return RegisteredEntity(entity_obj, self, self.reg_entity_id)

    def unregister(self, entity_obj):
        """ Unregister the objects
        """
        log.info("Unregistering resource with IoTCC {0}".format(entity_obj.ref_entity.name))

        def on_response(msg):
            try:
                log.debug("Received msg: {0}".format(msg))
                json_msg = json.loads(msg)
                log.debug("Processed msg: {0}".format(json_msg["type"]))
                if json_msg["type"] == "remove_resource_response" and json_msg["body"]["result"] == "succeeded":
                        log.info("Unregistration of resource {0} with IoTCC succeeded".format(entity_obj.ref_entity.name))
                else:
                        log.info("Unregistration of resource {0} with IoTCC failed".format(entity_obj.ref_entity.name))
            except:
                raise Exception("Exception while unregistering resource")

        self.comms.send(json.dumps(self._unregistration(self.next_id(), entity_obj.reg_entity_id)))
        on_response(self.recv_msg_queue.get(True,20))
        self.remove_reg_entity_details(entity_obj.ref_entity.name, entity_obj.reg_entity_id)
        if entity_obj.ref_entity.entity_type != "HelixGateway":
            self.store_device_info(entity_obj.reg_entity_id, entity_obj.ref_entity.name, entity_obj.ref_entity.entity_type, None, True)
        log.info("Unregistration of resource {0} with IoTCC complete".format(entity_obj.ref_entity.name))

    def create_relationship(self, reg_entity_parent, reg_entity_child):
        """ This function initializes all relations between Registered Entities.

            Parameters:
            - obj: The object that has just obtained an UUID
        """
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
            entity_obj = reg_entity_child.ref_entity
            self.publish_unit(reg_entity_child, entity_obj.name, entity_obj.unit)
        else:
            self.comms.send(json.dumps(self._relationship(self.next_id(),
                                                          reg_entity_parent.reg_entity_id,
                                                          reg_entity_child.reg_entity_id)))

    def _registration(self, msg_id, res_id, res_name, res_kind):
        return {
            "transactionID": msg_id,
            "type": "create_or_find_resource_request",
            "body": {
                "kind": res_kind,
                "id": res_id,
                "name": res_name
            }
        }

    def _relationship(self, msg_id, parent_res_uuid, child_res_uuid):
        return {
            "transactionID": msg_id,
            "type": "create_relationship_request",
            "body": {
                "parent": parent_res_uuid,
                "child": child_res_uuid
            }
        }

    def _properties(self, msg_id, res_uuid, res_kind, timestamp, properties):
        msg = {
            "transationID": msg_id,
            "type": "add_properties",
            "uuid": res_uuid,
            "body": {
                "kind": res_kind,
                "timestamp": timestamp,
                "property_data": []
            }
        }
        for key, value in properties.items():
            msg["body"]["property_data"].append({"propertyKey": key, "propertyValue": value})
        return msg

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
            "uuid": reg_metric.reg_entity_id,
            "metric_data": [{
                "statKey": reg_metric.ref_entity.name,
                "timestamps": _timestamps,
                "data": _values
            }]
        })

    def set_organization_group_properties(self, reg_entity_name, reg_entity_id, reg_entity_type, properties):
        log.info("Organization Group Properties defined for resource {0}".format(reg_entity_name))
        self.comms.send(json.dumps(
            self._properties(self.next_id(), reg_entity_id, reg_entity_type,
                             getUTCmillis(), properties)))

    def set_properties(self, reg_entity_obj, properties):
        # RegisteredMetric get parent's resid; RegisteredEntity gets own resid
        reg_entity_id = reg_entity_obj.reg_entity_id

        if isinstance(reg_entity_obj, RegisteredMetric):
            entity = reg_entity_obj.parent.ref_entity
        else:
            entity = reg_entity_obj.ref_entity

        log.info("Properties defined for resource {0}".format(entity.name))
        self.comms.send(json.dumps(
            self._properties(self.next_id(), reg_entity_id, entity.entity_type,
                             getUTCmillis(), properties)))
        if entity.entity_type == "HelixGateway":
            with self.file_ops_lock:
                self.store_reg_entity_attributes("EdgeSystem", entity.name,
                                                 reg_entity_obj.reg_entity_id, None, properties)
        else:
            # get dev_type, and prop_dict if possible
            with self.file_ops_lock:
                self.store_reg_entity_attributes("Devices", entity.name, reg_entity_obj.reg_entity_id,
                                                 entity.entity_type, properties)

    def publish_unit(self, reg_entity_obj, metric_name, unit):
        str_prefix, str_unit_name = parse_unit(unit)
        if not isinstance(str_prefix, basestring):
            str_prefix = ""
        if not isinstance(str_unit_name, basestring):
            str_unit_name = ""
        properties_added = {
            metric_name + "_unit": str_unit_name,
            metric_name + "_prefix": str_prefix
        }
        self.set_properties(reg_entity_obj, properties_added)
        log.info("Published metric unit with prefix to IoTCC")

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem)
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ")

    def _create_iotcc_json(self):
        msg = {
            "iotcc": {
                "EdgeSystem": {"SystemName": "", "EntityType": "", "uuid": ""},
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

    def store_reg_entity_details(self, entity_type, entity_name, reg_entity_id):
        msg = ''
        if self._iotcc_json == '':
            log.warn('iotcc.json file missing')
            return
        try:
            with open(self._iotcc_json, 'r') as f:
                msg = json.load(f)
            f.close()
        except IOError, err:
            log.error('Could not open {0} file '.format(self._iotcc_json) + str(err))
        log.debug('{0}:{1}'.format(entity_name, reg_entity_id))
        if entity_type == "HelixGateway":
            msg["iotcc"]["EdgeSystem"]["SystemName"] = entity_name
            msg["iotcc"]["EdgeSystem"]["uuid"] = reg_entity_id
            msg["iotcc"]["EdgeSystem"]["EntityType"] = entity_type
        else:
            entity_exist = False
            for device in msg["iotcc"]["Devices"]:
                if device["uuid"] == reg_entity_id and device["EntityType"] == entity_type and device[
                    "uuid"] == reg_entity_id:
                    entity_exist = True
                    break
            if not entity_exist:
                msg["iotcc"]["Devices"].append(
                    {"DeviceName": entity_name, "uuid": reg_entity_id, "EntityType": entity_type})
        if msg != '':
            with open(self._iotcc_json, 'w') as f:
                json.dump(msg, f, sort_keys=True, indent=4, ensure_ascii=False)
            f.close()

    def remove_reg_entity_details(self, entity_name, reg_entity_id):
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
        if msg["iotcc"]["EdgeSystem"]["SystemName"]==entity_name and msg["iotcc"]["EdgeSystem"]["uuid"]==reg_entity_id:
            del msg["iotcc"]["EdgeSystem"]
            log.info("Removed {0} edge-system from iotcc.json".format(entity_name))
        else:
            entity_exist = False
            for device in msg["iotcc"]["Devices"]:
                if device["uuid"] == reg_entity_id and device["uuid"] == reg_entity_id :
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

    def store_edge_system_info(self, uuid, name, prop_dict):
        """
        create (can overwrite) edge system info file of UUID.xml, with format of
        <attributes>
        <attribute name=attribute name value=attribute value/>
        …
        </attributes>
        except the first attribute is edge system name, all other attributes may vary
        """

        log.debug("store_edge_system_info")
        log.debug('{0}:{1}, prop_list: {2}'.format(uuid, name, prop_dict))
        root = ET.Element("attributes")
        # add edge system name as an attribute
        ET.SubElement(root, "attribute", name="edge system name", value=name)
        # add edge system properties as attributes
        if prop_dict is not None:
            for key in prop_dict.iterkeys():
                value = prop_dict[key]
                if key == 'entity type' or key == 'name' or key == 'device type':
                    continue
                ET.SubElement(root, "attribute", name=key, value=value)
        # add time stamp
        ET.SubElement(root, "attribute", name="LastSeenTimestamp",
                      value=strftime("%Y-%m-%dT%H:%M:%S", gmtime()))

        log.debug("store_edge_system_info dev_file_path:{0}".format(self.dev_file_path))
        file_path = self.dev_file_path + '/' + uuid + '.xml'
        with open(file_path, "w") as fp:
            fp.write(self.prettify(root))
        return

    def store_device_info(self, uuid, name, dev_type, prop_dict, remove_device):
        """
        create (can overwrite) device info file of device_UUID.json, with format of
        {
            "discovery":  {
                "remove" : false,
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
        # attribute_list.append(prop_dict)
        if prop_dict is not None:
            for key in prop_dict.iterkeys():
                value = prop_dict[key]
                if key == 'entity type' or key == 'name' or key == 'device type':
                    continue
                attribute_list.append({key: value})
        attribute_list.append({"LastSeenTimestamp": strftime("%Y-%m-%dT%H:%M:%S", gmtime())})
        log.debug('attribute_list: {0}'.format(attribute_list))
        msg = {
            "discovery": {
                "remove": remove_device,
                "attributes": attribute_list
            }
        }
        log.debug('msg: {0}'.format(msg))
        log.debug("store_device_info dev_file_path:{0}".format(self.dev_file_path))
        file_path = self.dev_file_path + '/' + uuid + '.json'
        try:
            with open(file_path, 'w') as f:
                json.dump(msg, f, sort_keys=True, indent=4, ensure_ascii=False)
                log.debug('Initialized ' + file_path)
            f.close()
        except IOError, err:
            log.error('Could not open {0} file '.format(file_path) + err)

    def write_entity_file(self, prop_dict, res_uuid):
        file_path = self.entity_file_path + '/' + res_uuid + '.json'
        try:
            with open(file_path, "w") as json_file:
                if (prop_dict is not None):
                    json_string = json.dumps(prop_dict)
                    json_file.write(json_string)
        except:
            log.error('Write file error')

    def read_entity_file(self, res_uuid):
        file_path = self.entity_file_path + '/' + res_uuid + '.json'
        prop_dict = None
        try:
            with open(file_path, "r") as json_file:
                prop_dict = json.loads(json_file.read())
        except:
            log.error('Read file error')
        return prop_dict

    def store_reg_entity_attributes(self, entity_type, entity_name, reg_entity_id,
                                    dev_type, prop_dict):
        log.debug('store_reg_entity_attributes\n {0}:{1}:{2}:{3}'.format(entity_type,
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
            tmp_dict = self.read_entity_file(reg_entity_id)
            if ((tmp_dict["entity type"] == entity_type) and (tmp_dict["name"] == entity_name)
                and (tmp_dict["device type"] == dev_type)):
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
        self.write_entity_file(new_prop_dict, reg_entity_id)
        ### Write IOTCC device file for AW agents
        if entity_type == "EdgeSystem":
            self.store_edge_system_info(reg_entity_id, entity_name, new_prop_dict)
        elif entity_type == "Devices":
            self.store_device_info(reg_entity_id, entity_name, dev_type, new_prop_dict, False)
        else:
            return

    def _get_file_storage_path(self, name):
        log.debug("_get_{0}".format(name))
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
                    log.debug("_get_{0} file_path:{1}".format(name, file_path))
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

    def next_id(self):
        self.counter = (self.counter + 1) & 0xffffff
        # Enforce even IDs
        return int(self.counter * 2)

    def _unregistration(self, msg_id, uuid):
        return {
            "transactionID": msg_id,
            "type": "remove_resource_request",
            "body": {
                "uuid": uuid
            }
        }
