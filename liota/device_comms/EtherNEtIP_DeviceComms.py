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
from liota.lib.transports.ENIP import EtherNetIP
import random

log = logging.getLogger(__name__)


class EtherNetDeviceComms(DeviceComms):
	"""
	DeviceComms for Can bus protocol
	"""

	def __init__(self, host=None, port=None, timeout=None, dialect=None, profiler=None, udp=False, broadcast=False, source_address=None):
		"""
		:param channel: The can interface identifier. Expected type is backend dependent.
		:param can_filters:A list of dictionaries each containing a "can_id" and a "can_mask".
			>>> [{"can_id": 0x11, "can_mask": 0x21}]
			A filter matches, when ``<received_can_id> & can_mask == can_id & can_mask``
		:param bustype: The ref:`bus` to listen too.
		:param listeners: An iterable of class:`can.Listeners`
		:param userdata: userdata is used to store messages coming from the receive channel.
		"""
		self.host = host
		self.port = port
		self.timeout = timeout
		self.dialect = dialect
		self.profiler = profiler
		self.udp = udp
		self.broadcast =broadcast
		self.source_address = source_address   


		if host is None:
			log.error("Host can't be none")
			raise TypeError("Host can't be None")

		self._connect()



	def _connect(self):
		self.client = EtherNetIP(self.host,self.port,self.timeout,self.dialect,self.profiler,self.udp,self.broadcast,self.source_address) 
		self.client.connect()

	def _disconnect(self):
		raise NotImplementedError


	def write(self,tag,elements,data,tag_type):

		if data is None:
			raise TypeError("Data can't be none")
		else:
			self.client.write(tag,elements,data,tag_type)
		

	def read(self):
		data = self.client.read()
		return data

	def send(self, message):
        	raise NotImplementedError

    	def receive(self):
        	raise NotImplementedError

	def shutdown():
		self.client.shutdown()
		
