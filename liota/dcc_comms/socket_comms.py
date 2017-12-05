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
import socket

from liota.dcc_comms.dcc_comms import DCCComms


log = logging.getLogger(__name__)


class SocketDccComms(DCCComms):
    """
    DccComms for BSD Socket transport.
    """

    def __init__(self, ip, port):
        """
        Init method for SocketDccComms.

        :param ip: IP address of the BSD socket server.
        :param port: Port number
        """
        self.ip = ip
        self.port = port
        self._connect()

    def _connect(self):
        """
        Establishes connection to the BSD socket server.
        :return:
        """
        self.client = socket.socket()
        log.info("Establishing Socket Connection")
        try:
            self.client.connect((self.ip, self.port))
            log.info("Socket Created")
        except Exception as ex:
            log.exception(
                "Unable to establish socket connection. Please check the firewall rules and try again.")
            self.client.close()
            self.client = None
            raise ex

    def _disconnect(self):
        """
        Disconnect from BSD socket server.
        TODO: To be implemented
        :return:
        """
        raise NotImplementedError

    def send(self, message, msg_attr=None):
        """
        Sends message to the BSD socket server.
        :param message: Message to be published
        :param msg_attr: MessagingAttribute.  It is 'None' for BSD Socket.
        :return:
        """
        log.debug("Publishing message:" + str(message))
        if self.client is not None:
            self.client.sendall(message)

    def receive(self, msg_attr=None):
        """
        Method to receive message from  BSD socket server.
        TODO: To be implemented
        :param msg_attr: MessagingAttributes.  It is 'None' for BSD Socket.
        :return:
        """
        raise NotImplementedError
