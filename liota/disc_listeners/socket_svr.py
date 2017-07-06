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
import socket
import thread
from threading import Thread
import logging
from liota.disc_listeners.discovery_listener import DiscoveryListener

log = logging.getLogger(__name__)

class SocketListener(DiscoveryListener):
    """
    SocketListener does inter-process communication (IPC), and
    blocks on a socket to listen to messages sent by devices.
    """

    def __init__(self, ip_port, name=None, discovery=None):
        super(SocketListener, self).__init__(name=name)

        host = ip_port.split(':')
        if host[1] is None:  # Reserve a port for your service.
            self.port = int(5000)
        else:
            self.port = int(host[1])
        self.host = 'localhost'
        log.debug("host:{0} port:{1}".format(self.host, self.port))
        self.sock = socket.socket()    # Create a socket object
        self.sock.bind((self.host, self.port)) # Bind to the port
        self.discovery = discovery
        log.info('SocketListener is initialized')
        print 'SocketListener is initialized'
        self.flag_alive = True
        self.start()

    def proc_dev_msg(self, payload):
        log.debug("socket_svr: proc_dev_msg")
        self.discovery.device_msg_process(payload)

    def on_new_client(self, conn, addr):
        while self.flag_alive:
            msg = conn.recv(1024)
            log.info('From {0} received {1}'.format(addr, msg))
            if msg == "":
                log.info('Socket from {0} closed remotely'.format(addr))
                break
            try:
                payload = json.loads(msg)
                Thread(target=self.proc_dev_msg, name="SocketMsgProc_Thread", args=(payload,)).start()
                msg = "Received~"
                conn.sendall(msg)
            except ValueError, err:
                # json can't be parsed
                log.error('Value: {0}, Error:{1}'.format(msg, str(err)))
                continue
        log.info('closing {0} connection socket {0}'.format(addr, conn))
        conn.close()

    def run(self):
        log.info('SocketListener Server started!')
        print 'SocketListener Server started!'
        log.info('Waiting for clients...')
        self.sock.listen(5)     # Now wait for client connection.
        self.conn_rec = []
        while self.flag_alive:
            conn, addr = self.sock.accept() # set connection with client
            log.info('Got connection from {0}'.format(addr))
            thread.start_new_thread(self.on_new_client, (conn, addr,))
            self.conn_rec.append(conn)
        self.sock.close()

    def clean_up(self):
        self.flag_alive = False
        for k in self.conn_rec[:]:
            if k is not None:
                k.close()
        if self.sock is not None:
            self.sock.close()
        log.info('Server is closed!')