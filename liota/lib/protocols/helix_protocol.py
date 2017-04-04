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
import json
import time

PROTOCOL_VERSION = "2.8"
log = logging.getLogger(__name__)


class HelixProtocolError(RuntimeError):
    pass


class HelixInitializationError(RuntimeError):
    pass


def require_field(container, field):
    if field not in container:
        raise HelixProtocolError("Missing {} field" % field)
        log.error("Missing {} field {0}", format(field))


class HelixProtocol:

    """
    Simple state machine for protocol to IoT Control Center adapter.
    States and messages:

    handshake_requested
    ===================================================
    --> Hello

    handshake_awaiting
    ===================================================
    <-- Hello

    handshake_verified
    ===================================================
    --> connection_request
    <-- connection_response

    """

    def __init__(self, con, user, password):
        self.con = con
        self.user = user
        self.password = password
        # `HandshakeAwaitingState.__init__` may be using `self.state`,
        # so initialize it.
        self.state = None
        self.state = HandshakeRequestedState(None, self)

    def on_receive(self, msg):
        if not self.state.on_receive(msg):
            raise HelixProtocolError("Unexpected Message " + msg["type"]
                                     + " during " + self.state.name)
            log.error("Unexpected Message {0}", msg["type"])

    def transition(self, state):
        self.state = state


class State:
    def __init__(self, previous, proto=None):
        if proto is None:
            proto = previous.proto
        self.proto = proto
        self.con = proto.con
        self.user = proto.user
        self.password = proto.password
        self.name = "Unknown State"
        if self.proto.state == previous:
            self.proto.transition(self)

    def is_active(self):
        return self == self.proto.state


class HandshakeRequestedState(State):
    def __init__(self, previous, proto=None):
        State.__init__(self, previous, proto)
        self.name = "HandshakeRequestedState"
        log.info("Sending message")
        self.con.send(json.dumps({
            "type": "hello"
        }))

    def on_receive(self, msg):
        log.debug("Received message in HandshakeRequestedState: {0}".format(msg))
        if msg["type"] == "hello":
            log.info("connection requested")
            HandshakeAwaitingState(self, msg)
            return True
        else:
            return False


class HandshakeAwaitingState(State):
    def __init__(self, previous, msg, proto=None):
        State.__init__(self, previous, proto)
        self.name = "HandshakeAwaitingState"
        require_field(msg, "transactionID")
        self.con.send(json.dumps({
            "type": "connection_request",
            "transactionID": msg["transactionID"],
            "body": {
                "version": PROTOCOL_VERSION,
                "username": self.user,
                "password": self.password
            }
        }))

    def on_receive(self, msg):
        log.debug("Received message in HandshakeAwaitingState: {0}".format(msg))
        if msg["type"] == "connection_response":
            require_field(msg["body"], "result")
            return True
        else:
            return False
