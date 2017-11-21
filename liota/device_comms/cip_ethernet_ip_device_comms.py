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

from liota.device_comms.device_comms import DeviceComms
from liota.lib.transports.cip_ethernet_ip import CipEthernetIp 
import random

log = logging.getLogger(__name__)


class CipEtherNetIpDeviceComms(DeviceComms):
    """
    DeviceComms for EtherNet/IP protocol
    """

    def __init__(
            self,
            host,
            port=None,
            timeout=None,
            dialect=None,
            profiler=None,
            udp=False,
            broadcast=False,
            source_address=None):
            
        """
	    :param host: CIP EtherNet/IP IP
	    :param port: CIP EtherNet/IP Port
	    :param timeout: Connection timeout
	    :param dialect: An EtherNet/IP CIP dialect, if not logix.Logix
	    :param profiler: If using a Python profiler, provide it to disable around I/O code
	    :param udp: Establishes a UDP/IP socket to use for request (eg. List Identity)
	    :param broadcast: Avoids connecting UDP/IP sockets; may receive many replies
	    :param source_address: Bind to a specific local interface (Default: 0.0.0.0:0)
	    
        """

        self.host = host
        self.port = port
        self.timeout = timeout
        self.dialect = dialect
        self.profiler = profiler
        self.udp = udp
        self.broadcast = broadcast
        self.source_address = source_address

        if host is None:
            raise TypeError("Host can't be None")

        self._connect()

    def _connect(self):
        self.client = CipEthernetIp(
            self.host,
            self.port,
            self.timeout,
            self.dialect,
            self.profiler,
            self.udp,
            self.broadcast,
            self.source_address)
        self.client.connect()

    def _disconnect(self):
        self.client.disconnect()

    def send(self, tag, elements, data, tag_type):
        if data is None:
            raise TypeError("Data can't be none")
        else:
            self.client.send(tag, elements, data, tag_type)

    def receive(self, tag, index):	
        data = self.client.receive(tag, index)
        return data

