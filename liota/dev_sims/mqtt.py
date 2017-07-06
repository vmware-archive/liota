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
import time
import logging

from liota.dev_sims.device_simulator import DeviceSimulator
from liota.device_comms.mqtt_device_comms import MqttDeviceComms
from liota.lib.utilities.identity import Identity
from liota.lib.utilities.tls_conf import TLSConf
from liota.lib.transports.mqtt import QoSDetails


log = logging.getLogger(__name__)


class MqttSimulator(DeviceSimulator):
    """
    MqttSimulator does inter-process communication (IPC), and
    publishes on topics to send simulated device beacon messages.
    """

    def __init__(self, mqtt_cfg, name=None, simulator=None):
        super(MqttSimulator, self).__init__(name=name)
        log.debug("MqttSimulator is initializing")

        broker_ip_port_topic = mqtt_cfg["broker_ip_port_topic"]
        str_list = broker_ip_port_topic.split(':')
        if str_list[0] == "" or str_list[0] == None:
            log.debug("No broker ip is specified!")
            self.broker_ip = "127.0.0.1"
        else:
            self.broker_ip = str(str_list[0])
        if str_list[1] == "" or str_list[1] == None:
            log.debug("No broker port is specified!")
        self.broker_port = int(str_list[1])
        if str_list[2] == "" or str_list[2] == None:
            log.debug("No broker topic is specified!")
        else:
            self.topic = str(str_list[2])
        self.simulator = simulator

        # Encapsulates Identity
        self.identity = Identity(mqtt_cfg['broker_root_ca_cert'], mqtt_cfg['broker_username'],
                                 mqtt_cfg['broker_password'], mqtt_cfg['edge_system_cert_file'],
                                 mqtt_cfg['edge_system_key_file'])
        if ((mqtt_cfg['cert_required'] == "None") or  (mqtt_cfg['cert_required'] == "CERT_NONE")):
            self.tls_conf = None
        else:
            # Encapsulate TLS parameters
            self.tls_conf = TLSConf(mqtt_cfg['cert_required'], mqtt_cfg['tls_version'], mqtt_cfg['cipher'])
        # Encapsulate QoS related parameters
        self.qos_details = QoSDetails(mqtt_cfg['in_flight'], int(mqtt_cfg['queue_size']), mqtt_cfg['retry'])
        # Create MQTT connection object with required params
        self.mqtt_conn = MqttDeviceComms(url=self.broker_ip, port=int(self.broker_port), identity=self.identity,
                                         tls_conf=self.tls_conf, qos_details=self.qos_details,  clean_session=True,
                                         keep_alive=int(mqtt_cfg['keep_alive']), enable_authentication=False)

        log.debug("MqttSimulator is initialized")
        print "MqttSimulator is initialized"
        self.cfg_sets = mqtt_cfg
        self.cnt = 0
        self.flag_alive = True
        self.start()

    def run(self):
        msg = {
            "Apple56": {
                "k1": "v1",
                "SN": "0",
                "kn": "vn"
            }
        }
        log.info('MqttSimulator is running')
        print "MqttSimulator is running"
        while self.flag_alive:
            if self.cnt >= 5:
                time.sleep(1000);
            else:
                msg["Apple56"]["SN"] = str(self.cnt)
                log.debug("send msg:{0}".format(msg))
                self.mqtt_conn.publish(self.topic, json.dumps(msg), 2, False)
                time.sleep(5)
            self.cnt += 1
            if self.cnt > 20:
                self.flag = False
        log.info("Thread exits: %s" % str(self.name))
        self.mqtt_conn._disconnect()

    def clean_up(self):
        self.flag_alive = False
        self.mqtt_conn._disconnect()