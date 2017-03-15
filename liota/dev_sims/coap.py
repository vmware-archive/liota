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
from coapthon.client.helperclient import HelperClient
from liota.dev_sims.device_simulator import DeviceSimulator

logg = logging.getLogger(__name__)

class Agent():

    def __init__(self, ip, port, path):
        self.ip = ip
        self.port = port
        self.path = path
        self.cnt = 0
        self.client = HelperClient(server=(ip, port))
        self.flag = True

    def getResource(self):
        response = self.client.get(self.path)
        logg.debug("getResouce response:{0}".format(response.pretty_print()))

    def putResource(self):
        msg = {
            "Banana23": {
                "k1": "v1",
                "serial": "0",
                "kn": "vn"
            }
        }
        while self.flag:
            if self.cnt >= 5:
                time.sleep(1000);
            else:
                msg["Banana23"]["serial"] = str(self.cnt)
                logg.debug("send msg:{0}".format(msg))
                payload = json.dumps(msg)
                response = self.client.put(self.path, payload)
                logg.debug("putResouce response:{0}".format(response.pretty_print()))
                time.sleep(5);
            self.cnt += 1
            if self.cnt > 20:
                self.flag = False

    def close(self):
        self.client.stop()

class CoapSimulator(DeviceSimulator):
    """
    CoapSimulator does inter-process communication (IPC), and
    sends simulated device beacon message.
    """

    def __init__(self, ip_port, name=None, simulator=None):
        super(CoapSimulator, self).__init__(name=name)
        str_list = ip_port.split(':')
        self.ip = str(str_list[0])
        if str_list[1] == "" or str_list[1] == None:
            logg.warning("No port is specified!")
            self.port = 5683
        else:
            self.port = int(str_list[1])
        self.simulator = simulator
        self.agent = Agent(self.ip, self.port, "message")

        logg.debug("CoapSimulator is initialized")
        print "CoapSimulator is initialized"
        self.flag_alive = True
        self.start()

    def run(self):
        if self.flag_alive:
            logg.info('CoapSimulator is running')
            print 'CoapSimulator is running'
            self.agent.putResource()
            while self.flag_alive:
                time.sleep(100)
        else:
            print "Thread exits"
        logg.info("Thread exits: %s" % str(self.name))

    def clean_up(self):
        self.flag_alive = False
        if (self.agent is not None):
            self.agent.close()