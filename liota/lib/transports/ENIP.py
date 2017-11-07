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
import os
import sys
import time
import cpppo
from random import randint
from cpppo.server.enip import client
from cpppo.server.enip.getattr import attribute_operations

log = logging.getLogger(__name__)

class EtherNetIP:
	'''
		CAN implementation for LIOTA. It uses python-can internally.
	'''
	def __init__(self, host=None, port=None, timeout=None, dialect=None, profiler=None, udp=False, broadcast=False, source_address=None):
		
		self.host = host
		self.port = port
		self.timeout = timeout
		self.dialect = dialect
		self.profiler = profiler
		self.udp = udp
		self.broadcast =broadcast
		self.source_address = source_address                                                                               
		

	def connect(self):
		self.conn = client.connector(host=self.host)
		if(self.conn):
			print("Connected to the server")
		 
		log.info("Connected to Server")


	def write(self,tag,elements,data,tag_type):
		self.tag = tag
		self.elements = elements
		self.data = data
		self.tag_type = tag_type

		try:
			req = self.conn.write( self.tag, elements=self.elements, data=self.data,
                              tag_type=self.tag_type)
		except AssertionError:
            		print "Response timed out!! Tearing Connection and Reconnecting!!!!!"
        	except AttributeError:
            		print "Tag J1_pos not written:::Will try again::"
        	except socket.error as exc:
            		print "Couldn't send command: %s" % ( exc )

 
    	def read(self):
        	req = self.conn.read("Scada[0]")
		assert self.conn.readable(), "Failed to receive reply"
		rpy = next(self.conn)
	 	data = rpy['enip']['CIP']['send_data']['CPF']['item'][1]['unconnected_send']['request']['read_frag']['data'][0]
        	return data
        	
	
	

	def shutdown( self ):
        	if not self.udp:
            		try:
                		self.conn.shutdown( socket.SHUT_WR )
            		except:
                		pass

	
