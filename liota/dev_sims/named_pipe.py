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
import time
import json
import stat
import fcntl
import inspect
import logging
from Queue import Queue

from liota.lib.utilities.utility import DiscUtilities
from liota.dev_sims.device_simulator import DeviceSimulator

log = logging.getLogger(__name__)

class NamedPipeSimulator(DeviceSimulator):
    """
    NamedPipeSimulatorThread does inter-process communication (IPC), and
    writes simulated device beacon message to a named pipe.
    """

    def __init__(self, pipe_file, name=None, simulator=None):
        super(NamedPipeSimulator, self).__init__(name=name)
        if DiscUtilities().validate_named_pipe(pipe_file) == False:
            return None
        self._pipe_file = pipe_file
        self.simulator = simulator # backpoint to simulator obj

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

        log.debug("NamedPipeSimulator is initialized")
        print "NamedPipeSimulator is initialized"
        self.cnt = 0
        self.flag_alive = True
        self.start()

    def run(self):
        msg = {
            "Press64": {
                "k1": "v1",
                "serial": "0",
                "kn": "vn"
            }
        }
        log.debug("NamedPipeSimulator is running")
        print "NamedPipeSimulator is running"
        while self.flag_alive:
            if self.cnt >= 5:
                time.sleep(1000);
            else:
                msg["Press64"]["serial"] = str(self.cnt)
                log.debug("send msg:{0}".format(msg))
                with open(self._pipe_file, "w+") as fp:
                    json_encode = json.dumps(msg)
                    fp.write(str(json_encode))
                    fp.write('\nEND\n')
                    time.sleep(5);
            self.cnt += 1
            if self.cnt > 20:
                self.flag = False
        log.info("Thread exits: %s" % str(self.name))

    def clean_up(self):
        self.flag_alive = False