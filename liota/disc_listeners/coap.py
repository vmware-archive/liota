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
import time
from threading import Thread

from coapthon.server.coap import CoAP
from coapthon.resources.resource import Resource
from liota.disc_listeners.discovery_listener import DiscoveryListener
from liota.lib.utilities.utility import LiotaConfigPath

logg = logging.getLogger(__name__)
LiotaConfigPath().setup_logging()

class MsgResource (Resource):

    def __init__(self, disc=None, name="MsgResource", coap_server=None):
        super(MsgResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = "Msg Resource"
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"
        self.disc = disc

    def render_PUT(self, request):
        logg.debug('PUT payload: {0}'.format(request.payload))
        # process received device messages'
        # better create another thread to process received messages
        try:
            payload = json.loads(request.payload)

            Thread(target=self.proc_dev_msg, name="CoapMsgProc_Thread", args=(payload, self.disc, )).start()
        except ValueError, err:
            # json can't be parsed
            logg.error('Value: {0}, Error:{1}'.format(request.payload, str(err)))

        self.edit_resource(request)
        return self

    def proc_dev_msg(self, payload, disc):
        logg.debug("proc_dev_msg payload:{0}".format(payload))
        disc.device_msg_process(payload)

    def render_GET(self, request):
        return self

class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False, disc=None):
        CoAP.__init__(self, (host, port), multicast)
        self.disc = disc
        self.add_resource('message/', MsgResource(disc=disc))

class CoapListener(DiscoveryListener):
    """
    CoapListener does inter-process communication (IPC), and
    waits to receive messages sent by devices.
    """

    def __init__(self, ip_port, name=None, discovery=None):
        super(CoapListener, self).__init__(name=name)
        str_list = ip_port.split(':')
        if str_list[0] == "" or str_list[0] == None:
            logg.warning("No ip is specified!")
            self.ip = "127.0.0.1"
        else:
            self.ip = str(str_list[0])
        if str_list[1] == "" or str_list[1] == None:
            logg.error("No port is specified!")
            self.port = 5683
        else:
            self.port = int(str_list[1])
        self.discovery = discovery
        self.flag_alive = True
        logg.debug("CoapListener is initialized")
        print "CoapListener is initialized"
        self.start()

    def run(self):
        if self.flag_alive:
            logg.info('CoapListerner is running')
            print 'CoapListerner is running'

            # start coap server
            self.server = CoAPServer(self.ip, self.port, multicast=False, disc=self.discovery)
            try:
                self.server.listen(10)
                while self.flag_alive:
                    time.sleep(100)
                logg.info("Thread exits: %s" % str(self.name))
            except KeyboardInterrupt:
                print "Server Shutdown"
                self.server.close()
                print "Exiting..."
        else:
            logg.info("Thread exits: %s" % str(self.name))
            print "Thread exits:", str(self.name)

    def clean_up(self):
        self.flag_alive = False
        if self.server is not None:
            self.server.close()
