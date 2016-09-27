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

from liota.dccs.dcc import DataCenterComponent
from liota.lib.protocols.helix_protocol import HelixProtocol
from liota.entities.metrics.metric import Metric
from liota.entities.systems.system import System
from liota.utilities.utility import getUTCmillis, LiotaConfigPath
from liota.utilities.si_unit import parse_unit
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.entities.registered_entity import RegisteredEntity

log = logging.getLogger(__name__)


class IotControlCenter(DataCenterComponent):
    """ The implementation of IoTCC cloud provider solution

    """

    def __init__(self, username, password, con):
        log.info("Logging into DCC")
        self.comms = con
        self.con = con.wss
        self.username = username
        self.password = password
        self.proto = HelixProtocol(self.con, username, password)

        def on_receive_safe(msg):
            try:
                log.debug("Received msg: {0}".format(msg))
                json_msg = json.loads(msg)
                self.proto.on_receive(json.loads(msg))
                log.debug("Processed msg: {0}".format(json_msg["type"]))
                if json_msg["type"] == "connection_verified":
                    log.info("Verified")
                    exit()
            except Exception:
                raise
                log.exception(
                    "Error received on connecting to DCC instance. Please verify the credentials and try again.")

        thread = threading.Thread(target=self.con.run)
        self.con.on_receive = on_receive_safe
        thread.daemon = True
        thread.start()
        thread.join()
        log.info("Logged in to DCC successfully")

    def register(self, entity_obj):
        """ Register the objects

        """
        if isinstance(entity_obj, Metric):
            self.publish_unit(entity_obj, entity_obj.name, entity_obj.unit)
            if entity_obj.parent is not None:
                reg_parent_entity_id = self.get_parent_reg_id(entity_obj.parent)
                return RegisteredMetric(entity_obj, self, reg_parent_entity_id)
        else:
            if not hasattr(entity_obj, "reg_entity_id"):
                log.info("Creating resource")
            log.info("Resource Name: {0}".format(entity_obj.name))

            def on_receive_safe(msg):
                try:
                    log.debug("Received msg: {0}".format(msg))
                    if msg != "":
                        json_msg = json.loads(msg)
                        self.proto.on_receive(json.loads(msg))
                        log.debug("Processed msg: {0}".format(json_msg["type"]))
                        if json_msg["type"] == "create_or_find_resource_response":
                            if json_msg["body"]["uuid"] != "null":
                                log.info("FOUND RESOURCE: {0}".format(json_msg["body"]["uuid"]))
                                self.reg_entity_id = json_msg["body"]["uuid"]
                                exit()
                            else:
                                log.info("Waiting for resource creation")
                                time.sleep(5)
                                self.con.send(
                                    self._registration(self.con.next_id(), entity_obj.entity_id, entity_obj.name,
                                                       entity_obj.entity_type))
                except:
                    raise

            thread = threading.Thread(target=self.con.run)
            self.con.on_receive = on_receive_safe
            thread.daemon = True
            thread.start()
            self.con.send(
                self._registration(self.con.next_id(), entity_obj.entity_id, entity_obj.name, entity_obj.entity_type))
            thread.join()
            log.info("Resource Registered {0}".format(entity_obj.name))
            if entity_obj.parent is not None:
                reg_parent_entity_id = self.get_parent_reg_id(entity_obj.parent)
                self._create_relationship(reg_parent_entity_id, self.reg_entity_id)
                log.info("Relationship Created")
            if entity_obj.entity_type == "IoT System":
                self.store_reg_entity_details(entity_obj, self.reg_entity_id, "System", 'w')
            else:
                self.store_reg_entity_details(entity_obj, self.reg_entity_id, entity_obj.name, 'a')
            return RegisteredEntity(entity_obj, self, self.reg_entity_id)

    def store_reg_entity_details(self, entity_obj, reg_entity_id, section_name, mode):
        config = ConfigParser.RawConfigParser()
        fullPath = LiotaConfigPath().get_liota_fullpath()
        if fullPath != '':
            try:
                if config.read(fullPath) != []:
                    try:
                        uuid_path = config.get('UUID_PATH', 'uuid_path')
                        uuid_config = ConfigParser.RawConfigParser()
                        uuid_config.optionxform = str
                        uuid_config.add_section(section_name)
                        uuid_config.set(section_name, 'name', entity_obj.name)
                        uuid_config.set(section_name, 'local_uuid', entity_obj.entity_id)
                        uuid_config.set(section_name, 'uuid', reg_entity_id)
                        with open(uuid_path, mode) as configfile:
                            uuid_config.write(configfile)
                    except ConfigParser.ParsingError, err:
                        log.error('Could not open config file')
                else:
                    raise IOError('Could not open config file ' + fullPath)
            except IOError, err:
                log.error('Could not open config file')
        else:
            # missing config file
            log.warn('liota.conf file missing')

    def get_parent_reg_id(self, entity_obj):
        config = ConfigParser.RawConfigParser()
        fullPath = LiotaConfigPath().get_liota_fullpath()
        if fullPath != '':
            try:
                if config.read(fullPath) != []:
                    try:
                        uuid_path = config.get('UUID_PATH', 'uuid_path')
                        uuid_config = ConfigParser.RawConfigParser()
                        uuid_config.optionxform = str
                        uuid_config.read(uuid_path)
                        if isinstance(entity_obj, System):
                            entity_obj_name = "System"
                        else:
                            entity_obj_name = entity_obj.name
                        stored_entity_id = uuid_config.get(entity_obj_name, "local_uuid")
                        if stored_entity_id == entity_obj.entity_id:
                            reg_parent_entity_id = uuid_config.get(entity_obj_name, "uuid")
                        return reg_parent_entity_id
                    except ConfigParser.ParsingError, err:
                        log.error('Could not open config file')
                else:
                    raise IOError('Could not open config file ' + fullPath)
            except IOError, err:
                log.error('Could not open config file')
        else:
            # missing config file
            log.warn('liota.conf file missing')

    def _create_relationship(self, entity_parent_reg_id, entity_child_reg_id):
        """ This function initializes all relations between System and it's children.
            It is called after each object's UUID is received.

            Parameters:
            - obj: The object that has just obtained an UUID
        """
        self.con.send(self._relationship(self.con.next_id(), entity_parent_reg_id, entity_child_reg_id))

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
        return {
            "type": "add_stats",
            "uuid": reg_metric.reg_entity_id,
            "metric_data": [{
                "statKey": reg_metric.ref_entity.name,
                "timestamps": _timestamps,
                "data": _values
            }],
        }

    def set_properties(self, entity_obj, properties):
        if isinstance(entity_obj, Metric):
            reg_entity_id = self.get_parent_reg_id(entity_obj.parent)
            reg_entity = entity_obj.parent
        else:
            reg_entity_id = entity_obj.reg_entity_id
            reg_entity = entity_obj.ref_entity
        log.info("Properties defined for resource {0}".format(reg_entity.name))
        self.con.send(
            self._properties(self.con.next_id(), reg_entity_id, reg_entity.entity_type,
                             getUTCmillis(), properties))

    def publish_unit(self, entity_obj, metric_name, unit):
        str_prefix, str_unit_name = parse_unit(unit)
        if not isinstance(str_prefix, basestring):
            str_prefix = ""
        if not isinstance(str_unit_name, basestring):
            str_unit_name = ""
        properties_added = {
            metric_name + "_unit": str_unit_name,
            metric_name + "_prefix": str_prefix
        }
        self.set_properties(entity_obj, properties_added)
        log.info("Published metric unit with prefix to IoTCC")
