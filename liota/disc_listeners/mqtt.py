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
from threading import Thread

from liota.disc_listeners.discovery_listener import DiscoveryListener
from liota.device_comms.mqtt_device_comms import MqttDeviceComms
from liota.lib.utilities.identity import Identity
from liota.lib.utilities.tls_conf import TLSConf
from liota.lib.transports.mqtt import QoSDetails

log = logging.getLogger(__name__)


class MqttListener(DiscoveryListener):
    """
    MqttListener does inter-process communication (IPC), and
    subscribe on topics to receive messages sent by devices.
    """
    def proc_dev_msg(self, payload):
        log.debug("mqtt_sub: proc_dev_msg")
        self.discovery.device_msg_process(payload)

    def callback_msg_proc(self, client, userdata, message):
        log.debug("MQTT received msg: {0}".format(message.payload))
        if message.payload != '':
            try:
                payload = json.loads(message.payload)
                Thread(target=self.proc_dev_msg, name="MqttMsgProc_Thread", args=(payload,)).start()
            except ValueError, err:
                # json can't be parsed
                log.error('Value: {0}, Error:{1}'.format(message.payload, str(err)))
                return

    def __init__(self, mqtt_cfg, name=None, discovery=None):
        super(MqttListener, self).__init__(name=name)
        broker_ip_port_topic = mqtt_cfg["broker_ip_port_topic"]
        str_list = broker_ip_port_topic.split(':')
        if str_list[0] == "" or str_list[0] == None:
            log.debug("No ip is specified!")
            self.broker_ip = "127.0.0.1"
        else:
            self.broker_ip = str(str_list[0])
        if str_list[1] == "" or str_list[1] == None:
            log.debug("No port is specified!")
        self.broker_port = int(str_list[1])
        if str_list[2] == "" or str_list[2] == None:
            log.debug("No topic is specified!")
        else:
            self.topic = str(str_list[2])
        log.debug("MqttListener is initialized")
        print "MqttListener is initialized"
        self.discovery = discovery

        self.cfg_sets = mqtt_cfg
        self.flag_alive = True
        self.start()

    def run(self):
        import copy

        if self.flag_alive:
            # Acquire resources from registry
            if (self.discovery is not None):
                try:
                    self.edge_system_object = copy.copy(self.discovery.pkg_registry.get("edge_system"))
                except:
                    log.exception("disc_listeners mqtt run exception")
                    return
            else:
                log.error("discovery.pkg_registry is None; could not start MqttListener!")
                return
            # Encapsulates Identity
            self.identity = Identity(self.cfg_sets['broker_root_ca_cert'], self.cfg_sets['broker_username'],
                                     self.cfg_sets['broker_password'],
                                     self.cfg_sets['edge_system_cert_file'], self.cfg_sets['edge_system_key_file'])

            if ((self.cfg_sets['cert_required'] == "None") or  (self.cfg_sets['cert_required'] == "CERT_NONE")):
                self.tls_conf = None
            else:
                # Encapsulate TLS parameters
                self.tls_conf = TLSConf(self.cfg_sets['cert_required'], self.cfg_sets['tls_version'],
                                        self.cfg_sets['cipher'])
            # Encapsulate QoS related parameters
            self.qos_details = QoSDetails(self.cfg_sets['in_flight'], int(self.cfg_sets['queue_size']), self.cfg_sets['retry'])

            # Create MQTT connection object with required params
            self.mqtt_conn = MqttDeviceComms(url=self.broker_ip, port=int(self.broker_port), identity=self.identity,
                                             tls_conf=self.tls_conf, qos_details=self.qos_details, clean_session=True,
                                             keep_alive=int(self.cfg_sets['keep_alive']),
                                             enable_authentication=self.cfg_sets['enable_authentication'])
            # Add callback methods
            self.mqtt_conn.subscribe(self.topic, 2, self.callback_msg_proc)
            log.debug("MqttListener is running")
            print "MqttListener is running"
        else:
            log.info("Thread exits: %s" % str(self.name))
            self.mqtt_conn._disconnect()

    def clean_up(self):
        self.flag_alive = False
        self.mqtt_conn._disconnect()
