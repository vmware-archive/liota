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


PROTOCOL_VERSION = "2.7"
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

    handshake_awaiting
    ===================================================
    <-- connection_request

    handshake_responded
    ===================================================
    --> connection_response
    <-- connection_verified

    handshake_verified
    ===================================================
    for all output resource kinds simultaneously do
        --> create_resource_kind_request
        <-- create_resource_kind_response

    steady
    ===================================================
    for all objects simultaneously do
        while uuid not available do
            --> create_or_find_resource_request
            <-- create_or_find_resource_response
        // Create relationship to gateway
        --> create_relationship_request
        <-- create_relationship_response

        loop forever
            if output
                <-- action
            if input
                --> add_stats
    """

    def __init__(self, con, user, password):
        self.con = con
        self.user = user
        self.password = password
        # `HandshakeAwaitingState.__init__` may be using `self.state`,
        # so initialize it.
        self.state = None
        self.state = HandshakeAwaitingState(None, self)

    def on_receive(self, msg):
        require_field(msg, "type")
        require_field(msg, "body")

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


class HandshakeAwaitingState(State):

    def __init__(self, previous, proto=None):
        State.__init__(self, previous, proto)
        self.name = "HandshakeAwaitingState"

    def on_receive(self, msg):
        log.debug(
            "Received message in HandshakeAwaitingState: {0}".format(msg))
        if msg["type"] == "connection_request":
            HandshakeRequestedState(self, msg)
            return True
        else:
            return False


class HandshakeRequestedState(State):

    def __init__(self, previous, msg, proto=None):
        State.__init__(self, previous, proto)
        self.name = "HandshakeRequestedState"
        require_field(msg, "transactionID")
        self.con.send({
            "type": "connection_response",
            "transactionID": msg["transactionID"],
            "body": {
                "version": PROTOCOL_VERSION,
                "username": self.user,
                "password": self.password
            }
        })

    def on_receive(self, msg):
        log.debug(
            "Received message in HandshakeRequestedState: {0}".format(msg))
        if msg["type"] == "connection_verified":
            require_field(msg["body"], "result")

            if msg["body"]["result"] == "succeeded":
                HandshakeVerifiedState(self)
                return True
            else:
                raise HelixInitializationError("Handshake Failed")
                log.error("Handshake Failed")
        else:
            return False


class HandshakeVerifiedState(State):

    def __init__(self, previous, proto=None):
        State.__init__(self, previous, proto)
        self.name = "HandshakeVerifiedState"
        log.info("Handshake Verified with DCC")
        SteadyState(self)

    def on_receive(self, msg):
        if msg["type"] == "create_resource_kind_response":
            require_field(msg["body"], "result")
            require_field(msg, "transactionID")

            if msg["body"]["result"] == "succeeded" or msg["body"]["result"] \
                    == "exists":
                search = [obj for obj in self.obj_list
                          if obj.extra.get("kind_req") == msg["transactionID"]]
                if search:
                    search[0].extra["kind_registered"] = True
                    search[0].extra["kind_req"] = None
                    self.pending_kinds -= 1
                    if self.pending_kinds == 0:
                        SteadyState(self)
                return True
            elif msg["body"]["result"] == "pending":
                search = [obj for obj in self.obj_list
                          if obj.extra.get("kind_req") == msg["transactionID"]]
                if search:
                    search[0].extra["kind_req"] = None
                return True
            else:
                raise HelixInitializationError("Resource Kind Creation Failed")
                log.error("Resource Kind Creation Failed")
        return False


class SteadyState(State):

    def __init__(self, previous, proto=None):
        State.__init__(self, previous, proto)
        self.name = "SteadyState"
        self.action_map = {}
        log.debug("Entered steady state")

    def trigger_action(self, uuid, value):
        if uuid not in self.action_map:
            # ignore unknown actions
            pass
        else:
            handler = self.action_map[uuid]
            handler.on_change(value)

    def on_receive(self, msg):
        log.debug("IN ON_RECEIVE")
        if msg["type"] == "create_or_find_resource_response":
            require_field(msg["body"], "uuid")
            require_field(msg, "transactionID")

            res_uuid = msg["body"]["uuid"]
            return True

        elif msg["type"] == "action":
            require_field(msg["body"], "uuid")
            require_field(msg["body"], "code")

            self.trigger_action(msg["body"]["uuid"], msg["body"]["code"])
            return True

        elif msg["type"] == "create_relationship_response":
            # Not checked right now
            return True

        else:
            return False
