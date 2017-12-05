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

from abc import ABCMeta, abstractmethod


class DCCComms:

    """
    Abstract base class for all DCC communications.
    """
    __metaclass__ = ABCMeta

    # -----------------------------------------------------------------------
    # If a specific DCCComms has parameters to establish connection, pass
    # them to its constructor, not self._connect. Keep self._connect free of
    # external arguments.
    #
    @abstractmethod
    def __init__(self):
        """
        Abstract init method for DCCComms (Data Center Component Communication Protocols).

        This must take all necessary params to establish a connection and must call _connect().
        """
        self._connect()

    @abstractmethod
    def _connect(self):
        """
        Abstract method for protocol specific connection establishment implementation.

        All sub-classes implementing this method MUST assign the established connection to the variable 'self.client'
        (Eg:) self.client = MyProtocol(ip, port, credentials)

        :return:
        """
        pass

    @abstractmethod
    def _disconnect(self):
        """
        Abstract method for protocol-specific disconnect implementation.
        :return:
        """
        pass

    @abstractmethod
    def send(self, message, msg_attr):
        """
        Abstract method to send message over the established connection.

        :param message: Message to be sent
        :param msg_attr: MessagingAttributes object.  Message oriented protocols require params like QoS, RoutingKey,
                        Topics, etc.,  Such parameters should be encapsulated into protocol specific objects.
                        Eg: MqttMessagingAttributes, AmqpMessagingAttributes
        :return:
        """
        pass

    @abstractmethod
    def receive(self, msg_attr):
        """
        Abstract method to receive message from the DCC.

        :param msg_attr: MessagingAttributes object.  Message oriented protocols require params like QoS, RoutingKey,
                        Topics, Callbacks, etc.,  Such parameters should be encapsulated into protocol specific objects.
                        Eg: MqttMessagingAttributes, AmqpMessagingAttributes
        :return:
        """
        pass
