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
import os
import sys
import json
import stat
import time
import fcntl
import inspect
import logging
from Queue import Queue
from threading import Thread

from twisted.internet.defer import Deferred
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.python import log

import txthings.coap as coap
import txthings.resource as resource

from liota.dev_sims.device_simulator import DeviceSimulator

logg = logging.getLogger(__name__)

class Agent():
    """
    Example class which performs single PUT request to iot.eclipse.org
    port 5683 (official IANA assigned CoAP port), URI "/large-update".
    Request is sent 1 second after initialization.

    Payload is bigger than 64 bytes, and with default settings it
    should be sent as several blocks.
    """

    def __init__(self, protocol, ip, port):
        self.protocol = protocol
        reactor.callLater(1, self.putResource)
        self.ip = ip
        self.port = port
        self.cnt = 0
        self.flag = True

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
                request = coap.Message(code=coap.PUT, payload=payload)
                request.opt.uri_path = ("messages",)
                request.opt.content_format = coap.media_types_rev['text/plain']
                request.remote = (self.ip, self.port)
                d = self.protocol.request(request)
                d.addCallback(self.printResponse)
                time.sleep(5);
            self.cnt += 1
            if self.cnt > 20:
                self.flag = False

    def printResponse(self, response):
        logg.warnings('Response Code: {0}'.format(coap.responses[response.code]))
        logg.warnings('Payload: {0}'.format(response.payload))

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
            logg.error("No port is specified!")
            self.port = coap.COAP_PORT
        else:
            self.port = int(str_list[1])
        logg.debug("coap_init:{0}:{1}".format(self.ip, self.port))
        self.simulator = simulator

        #log.startLogging(sys.stdout)
        self.endpoint = resource.Endpoint(None)
        self.protocol = coap.Coap(self.endpoint)
        self.client = Agent(self.protocol, self.ip, self.port)

        logg.debug("CoapSimulator is initialized")
        print "CoapSimulator is initialized"
        self.flag_alive = True
        self.start()

    def run(self):
        if self.flag_alive:
            logg.info('CoapSimulator is running')
            print 'CoapSimulator is running'
            reactor.listenUDP(61616, self.protocol)
            Thread(target=reactor.run, name="CoapSimulator_Thread", args=(False,)).start()
            while self.flag_alive:
                time.sleep(100)
            logg.info("Thread exits: %s" % str(self.name))
        else:
            logg.info("Thread exits: %s" % str(self.name))

    def clean_up(self):
        self.flag_alive = False
        if (self.protocol is not None) and (self.client is not None):
            reactor.stop()