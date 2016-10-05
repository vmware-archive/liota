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

log = logging.getLogger(__name__)


class WebSocket():
    """ WebSocket class implementation

    """

    def __init__(self, url):
        self.url = url
        self.connect_soc()

    def connect_soc(self):
        try:
            self.WebSocketConnection(self.url, False)
            log.info("Connection Successful")
        except Exception:
            log.exception("WebSocket exception, please check the WebSocket address and try again.")
            sys.exit(0)

    # CERTPATH to be taken in consideration later
    def WebSocketConnection(self, host, verify_cert=True, CERTPATH="/etc/liota/cert"):
        self.counter = 0
        if not verify_cert:
            self.ws = None
            self.ws = create_connection(host, enable_multithread=True,
                                        sslopt={"cert_reqs": ssl.CERT_NONE})
        else:
            self.ws = None
            if os.path.isfile(CERTPATH):
                try:
                    self.ws = create_connection(host, enable_multithread=True,
                                                sslopt={"cert_reqs": ssl.CERT_REQUIRED,
                                                        "ca_certs": CERTPATH})
                except ssl.SSLError:
                    pass
            if self.ws is None:
                raise (IOError("Couldn't verify host certificate"))

    def run(self):
        try:
            log.info("Stream Opened")
            while True:
                msg = self.ws.recv()
                log.debug("Message received while running {0}".format(msg))
                if msg is "":
                    log.error("Stream Closed")
                    raise Exception("No message received from the server, please check the connection and the DCC credentials.")
                log.debug("RX {0}".format(msg))
                if self.on_receive is not None:
                    self.on_receive(msg)
        except Exception:
            log.exception("Exception on receiving the response from Server, please check the connection and try again.")
            self.close()
            os._exit(0) # need to revisit this

    def send(self, msg):
        request_calls = ['request', 'response']
        complete_message = json.dumps(msg)
        log.debug("Sending data to DCC")
        log.debug("TX Sending message {0}".format(complete_message))
        try:
            self.ws.send(complete_message)
        except:
            # Retry logic only for publishing stats, not for request or response calls
            if all(request not in complete_message for request in request_calls):
                attempts = 1
                while attempts < 4:
                    try:
                        log.debug("Exception while sending data, applying retry logic.")
                        self.connect_soc()
                        log.info("Created New Websocket")
                        log.debug("TX Sending message {0}".format(complete_message))
                        self.ws.send(complete_message)
                        break
                    except:
                        # Three times retry websocket connection for publishing data
                        log.info("{0} attempt".format(attempts))
                        attempts += 1
                        if attempts == 4:
                            # os._exit used as websocket connection is not created even after the fourth retry
                            log.exception("Exception while sending data, please check the connection and try again.")
                            self.close()
                            os._exit(0)
            else:
                log.exception("Exception while sending data, please check the connection and try again.")
                self.close()
                sys.exit(0)

    def next_id(self):
        self.counter = (self.counter + 1) & 0xffffff
        # Enforce even IDs
        return self.counter * 2

    def close(self):
        if self.ws is not None:
            self.ws.close()
        log.debug("Connection closed, cleanup done")
