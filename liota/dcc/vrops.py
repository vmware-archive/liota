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
import ConfigParser

from liota.dcc.dcc_base import DataCenterComponent
from helix_protocol import HelixProtocol
from liota.core.metric_handler import Metric
from liota.utilities.utility import getUTCmillis, LiotaConfigPath
from liota.utilities.si_unit import parse_unit


log = logging.getLogger(__name__)

class Vrops(DataCenterComponent):
    """ The implementation of vROPS cloud provider solution

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
                if json_msg["type"] == "connection_verified":
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
            vrops_res = self.VropsResource(gw)
            log.info("Creating resource")
            log.info("Resource Name: {0}".format(gw.res_name))
            def on_receive_safe(msg):
                try:
                    log.debug("Received msg: {0}".format(msg))
                    if msg != "":
                       json_msg = json.loads(msg)
                       self.proto.on_receive(json.loads(msg))
                       log.debug("Processed msg: {0}".format(json_msg["type"]))
                       if json_msg["type"] == "create_or_find_resource_response" :
                           if json_msg["body"]["uuid"] != "null":
                               log.info("FOUND RESOURCE: {0}".format(json_msg["body"]["uuid"]))
                               gw.res_uuid = json_msg["body"]["uuid"]
                               vrops_res.registered = True
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
            if gw.res_kind is 'HelixGateway':
                config = ConfigParser.RawConfigParser()
                fullPath = LiotaConfigPath().get_liota_fullpath()
                if fullPath != '':
                    try:
                        if config.read(fullPath) != []:
                            try:
                                uuid_path = config.get('UUID_PATH', 'uuid_path')
                                uuid_config = ConfigParser.RawConfigParser()
                                uuid_config.add_section('GATEWAY')
                                uuid_config.set('GATEWAY', gw.res_name, gw.res_uuid)
                                with open(uuid_path, 'w') as configfile:
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
            return vrops_res

    def connect_soc(self, protocol, url, user_name, password):
        pass

    def subscribe(self):
        pass

    def publish(self, metric):
        timestamps = [t for t, _ in metric.values]
        values = [v for _, v in metric.values]
        message = metric.gw._report_data(self.con.next_id(), metric.details, timestamps, values)
        self.con.send(message)

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

    def properties(self, msg_id, res_uuid, res_kind, timestamp, properties):
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
            msg["body"]["property_data"].append({"propertyKey": key, "propertyValue":  value})
        return msg

    def set_properties(self, registered_gw, properties):
        log.info("Properties defined for resource {0}".format(registered_gw.resource.res_name))
        self.con.send(self.properties(self.con.next_id(), registered_gw.resource.res_uuid, registered_gw.resource.res_kind, getUTCmillis(), properties))

    class VropsResource:

        def __init__(self, resource, registered=False):
            self.resource = resource
            self.registered = registered

    def publish_unit(self, registered_gw, metric_name, unit):
        str_prefix, str_unit_name = parse_unit(unit)
        if not isinstance(str_prefix, basestring):
            str_prefix = ""
        if not isinstance(str_unit_name, basestring):
            str_unit_name = ""
        properties_added = {
                metric_name + "_unit": str_unit_name,
                metric_name + "_prefix": str_prefix
            }
        self.set_properties(registered_gw, properties_added)
        log.info("Published metric unit with prefix to vROps")

