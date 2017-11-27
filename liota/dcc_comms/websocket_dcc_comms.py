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
import logging
import Queue
from liota.lib.transports.web_socket import WebSocket

from liota.dcc_comms.dcc_comms import DCCComms


log = logging.getLogger(__name__)


class WebSocketDccComms(DCCComms):
    """
    DccComms implementation for WebSocket Transport.
    """

    def __init__(self, url, verify_cert, identity=None):
        """
        Init method for WebSocketDccComms

        :param url: WebScoket server URL
        :param verify_cert: Boolean value to verify certificate or not
        :param identity: Identity Object
        """
        self.url = url
        self.verify_cert = verify_cert
        self.identity = identity
        self.userdata = Queue.Queue()
        self._connect()

    def _connect(self):
        """
        Establishes connection with a WebSocket server.
        :return:
        """
        self.client = WebSocket(self.url, self.verify_cert, self.identity)

    def _disconnect(self):
        """
        Disconnects from WebSocket server.
        TODO: To be implemented
        :return:
        """
        raise NotImplementedError

    def send(self, message, msg_attr=None):
        """
        Sends message to the WebSocket Server.

        :param message: Message to be sent.
        :param msg_attr: MessagingAttributes Object.  It is 'None' for WebSocket.
        :return:
        """
        self.client.send(message)

    def receive(self, msg_attr=None):
        """
        Receives message from WebSocket Server in a blocking manner.

        :param msg_attr: MessagingAttributes.  It is 'None' for WebSocket.
        :return:
        """
        self.client.receive(self.userdata)
