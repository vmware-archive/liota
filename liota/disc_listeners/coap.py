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
import os
import sys
import json
import stat
import time
import fcntl
import thread
import logging
import inspect
import datetime
from Queue import Queue
from threading import Thread

from twisted.internet import defer
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.python import log

import txthings.resource as resource
import txthings.coap as coap

from liota.disc_listeners.discovery_listener import DiscoveryListener

logg = logging.getLogger(__name__)

class MsgResource (resource.CoAPResource):

    def __init__(self, disc):
        resource.CoAPResource.__init__(self)
        self.visible = True
        self.addParam(resource.LinkParam("title", "Message resource"))
        self.disc = disc

    def render_PUT(self, request):
        logg.debug('PUT payload: {0}'.format(request.payload))
        # process received device messages'
        # better create another thread to process received messages
        try:
            payload = json.loads(request.payload)
            Thread(target=self.proc_dev_msg, name="CoapMsgProc_Thread", args=(payload,)).start()
            payload = "Received~"
        except ValueError, err:
            # json can't be parsed
            logg.error('Value: {0}, Error:{1}'.format(request.payload, str(err)))
            payload = "Received wrong message (no jason message)"

        # send response
        response = coap.Message(code=coap.CHANGED, payload=payload)
        return defer.succeed(response)

    def proc_dev_msg(self, payload):
        self.disc.device_msg_process(payload)

class CoreResource(resource.CoAPResource):
    """
    Example Resource that provides list of links hosted by a server.
    Normally it should be hosted at /.well-known/core

    Resource should be initialized with "root" resource, which can be used
    to generate the list of links.

    For the response, an option "Content-Format" is set to value 40,
    meaning "application/link-format". Without it most clients won't
    be able to automatically interpret the link format.

    Notice that self.visible is not set - that means that resource won't
    be listed in the link format it hosts.
    """

    def __init__(self, root):
        resource.CoAPResource.__init__(self)
        self.root = root

    def render_GET(self, request):
        data = []
        self.root.generateResourceList(data, "")
        payload = ",".join(data)
        logg.debug("coap_svr Get: {0}".format(payload))
        response = coap.Message(code=coap.CONTENT, payload=payload)
        response.opt.content_format = coap.media_types_rev['application/link-format']
        return defer.succeed(response)


class CoapListener(DiscoveryListener):
    """
    CoapListener does inter-process communication (IPC), and
    waits to receive messages sent by devices.
    """

    def __init__(self, ip_port, name=None, discovery=None):
        super(CoapListener, self).__init__(name=name)
        str_list = ip_port.split(':')
        if str_list[1] == "" or str_list[1] == None:
            logg.error("No port is specified!")
            self.port = coap.COAP_PORT
        else:
            self.port = int(str_list[1])
        self.discovery = discovery

        # Resource tree creation
        #log.startLogging(sys.stdout)
        self.root = resource.CoAPResource()

        well_known = resource.CoAPResource()
        self.root.putChild('.well-known', well_known)
        core = CoreResource(self.root)
        well_known.putChild('core', core)

        self.msg = MsgResource(discovery)
        self.root.putChild('messages', self.msg)

        logg.debug("CoapListener is initialized")
        print "CoapListener is initialized"
        self.flag_alive = True
        self.start()

    def run(self):
        if self.flag_alive:
            logg.info('CoapListerner is running')
            print 'CoapListerner is running'
            self.endpoint = resource.Endpoint(self.root)
            reactor.listenUDP(self.port, coap.Coap(self.endpoint))
            Thread(target=reactor.run, name="CoapListerner_Thread", args=(False,)).start()
            while self.flag_alive:
                time.sleep(100)
            logg.info("Thread exits: %s" % str(self.name))
        else:
            logg.info("Thread exits: %s" % str(self.name))

    def clean_up(self):
        self.flag_alive = False
        if self.endpoint is not None:
            reactor.stop()
