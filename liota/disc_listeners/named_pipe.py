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
import fcntl
import thread
import logging
from Queue import Queue
from threading import Thread

from liota.lib.utilities.utility import DiscUtilities
from liota.disc_listeners.discovery_listener import DiscoveryListener

log = logging.getLogger(__name__)

class NamedPipeListener(DiscoveryListener):
    """
    NamedPipeMessengerThread does inter-process communication (IPC), and
    blocks on a named pipe to listen to messages casted by devices.
    """

    def __init__(self, pipe_file, name=None, discovery=None):
        super(NamedPipeListener, self).__init__(name=name)
        if DiscUtilities().validate_named_pipe(pipe_file) == False:
            return None
        self._pipe_file = pipe_file
        self.msg_queue = Queue()
        self.discovery = discovery # backpoint to discovery obj

        # Unblock previous writers
        BUFFER_SIZE = 65536
        ph = None
        try:
            ph = os.open(self._pipe_file, os.O_RDONLY | os.O_NONBLOCK)
            flags = fcntl.fcntl(ph, fcntl.F_GETFL)
            flags &= ~os.O_NONBLOCK
            fcntl.fcntl(ph, fcntl.F_SETFL, flags)
            while True:
                buffer = os.read(ph, BUFFER_SIZE)
                if not buffer:
                    break
        except OSError as err:
            import errno
            if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
                pass  # It is supposed to raise one of these exceptions
            else:
                raise err
        finally:
            if ph:
                os.close(ph)
        log.debug('NamedPipeListener is initialized')
        print 'NamedPipeListener is initialized'
        self.flag_alive = True
        self.start()

    def proc_dev_msg(self, payload):
        log.debug("named_pipe: proc_dev_msg")
        self.discovery.device_msg_process(payload)

    def run(self):
        log.info('NamedPipeListener is running')
        print 'NamedPipeListener is running'
        while self.flag_alive:
            with open(self._pipe_file, "r") as fp:
                data = ''
                for line in fp.readlines():
                    if line != 'END\n':
                        data += line
                    else:
                        try:
                            log.info('Received {0}'.format(data))
                            payload = json.loads(data)
                            Thread(target=self.proc_dev_msg, name="PipeMsgProc_Thread", args=(payload,)).start()
                            data = ''
                        except ValueError, err:
                            # json can't be parsed
                            log.error('Value: {0}, Error:{1}'.format(data, str(err)))
                            continue
        log.info("Thread exits: %s" % str(self.name))

    def clean_up(self):
        self.flag_alive = False