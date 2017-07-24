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
import socket
import time

from liota.dev_sims.device_simulator import DeviceSimulator

log = logging.getLogger(__name__)

class SocketSimulator(DeviceSimulator):
    """
    SocketSimulator does inter-process communication (IPC), and
    sends simulated device beacon message.
    """
    def __init__(self, ip_port, name, simulator):
        super(SocketSimulator, self).__init__(name=name)
        str_list = ip_port.split(':')
        self.ip = str_list[0]
        if str_list[1] == "" or str_list[1] == None:
            log.error("No port is specified!")
            return
        self.port = int(str_list[1])
        self.simulator = simulator # backpoint to simulator obj
        self._connect()

    def _connect(self):
        self.sock = socket.socket()
        log.info("Establishing Socket Connection")
        try:
            self.sock.connect((self.ip, self.port))
            log.info("Socket Created")
        except Exception as ex:
            log.exception(
                "Unable to establish socket connection. Please check the firewall rules and try again.")
            self.sock.close()
            self.sock = None
            raise ex
        log.debug("SocketSimulator is initialized")
        print "SocketSimulator is initialized"
        self.cnt = 0
        self.flag_alive = True
        self.start()

    def clean_up(self):
        self.flag_alive = False
        self.sock.close()

    def send(self, message):
        self.sock.send(message)

    def run(self):
        log.info('SocketSimulator is running...')
        print 'SocketSimulator is running...'
        while self.flag_alive:
            msg = {
                "LM35": {
                    "k1": "v1",
                    "SN": "0",
                    "kn": "vn"
                }
            }
            if self.cnt >= 5:
                time.sleep(1000);
            else:
                msg["LM35"]["SN"] = str(self.cnt)
                log.debug("send msg:{0}".format(msg))
                self.sock.sendall(json.dumps(msg))
                time.sleep(5)
            self.cnt += 1
            if self.cnt > 20:
                self.flag = False
        log.info('closing %s connection socket %s'.format(self.ip, self.sock))
        self.sock.close()