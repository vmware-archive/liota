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
import os
import ssl
import sys
from websocket import create_connection

from transport_layer_base import TransportLayer

PIDFILE = "/var/run/helix-agent.pid"
CERTDIR = "/var/lib/helix-agent/cert"
log = logging.getLogger(__name__)

class WebSocket(TransportLayer):
    """ WebSocket class implementation

    """
    def __init__(self, ip_address, port, secure):
        if port is not None:
            ip_address = ip_address + ':' + port
        url = ip_address + '/helix'
        TransportLayer.__init__(self, url, secure)

    def connect_soc(self):
        try:
            self.VropsConnection(self.url, False)
            log.info("Connection Successful")
        except Exception:
            log.exception("WebSocket exception, please check the WebSocket address and try again.")
            sys.exit(0)


    def VropsConnection(self, host, verify_cert=True):

      if not verify_cert:
#          self.ws = create_connection(host,
#             sslopt={"cert_reqs": ssl.CERT_NONE})
            self.ws = create_connection(host, enable_multithread=True,
              sslopt={"cert_reqs": ssl.CERT_NONE},
              header=["Authorization: Bearer dummyToken"])
      else:
         self.ws = None
         for filename in os.listdir(CERTDIR):
            if os.path.isfile(CERTDIR + "/" + filename):
               try:
                  self.ws = create_connection(host, enable_multithread=True,
                     sslopt={"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": CERTDIR + "/" + filename},
                     header=["Authorization: Bearer dummyToken"])
                  break
#               except CertificateError, ssl.SSLError:
               except ssl.SSLError:
                  pass
         if self.ws is None:
            raise(IOError("Couldn't verify host certificate"))

      self.counter = 0

    def run(self):
        try:
            log.debug("Stream Opened")
            while True:
                msg = self.ws.recv()
                log.debug ("Message received while running {0}".format(msg))
                if msg is "":
                    # TO DO: Check if os._exit(0) is required
                    log.error("Stream Closed")
                    log.error("Please check the DCC credentials and try again.")
                    os._exit(0)
                    break
                log.debug("RX {0}".format(msg))
                if self.on_receive is not None:
                    self.on_receive(msg)
        except Exception:
            log.exception("Exception on receiving the response from Server, please check the connection and try again.")
            self.close()
            os._exit(0)

    def send(self, msg):
      s = json.dumps(msg)
      log.info("TX Sending message {0}".format(s))
      try:
          self.ws.send(s)
      except Exception:
          log.exception("Exception while sending data, please check the connection and try again.")
          self.close()
          # TO DO Check if required
          os._exit(0)

    def next_id(self):
      self.counter = (self.counter + 1) & 0xffffff
      # Enforce even IDs
      return self.counter * 2

    def close(self):
      if self.ws is not None:
          self.ws.close()
      log.info("Connection closed, cleanup done")

