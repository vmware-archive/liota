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
import threading
import time

from cloud_provider_base import CloudProvider

log = logging.getLogger(__name__)

class Graphite(CloudProvider):

    def __init__(self, socket_obj):
        self.sock = socket_obj.sock
        pass

    def create_metric(self, gw, details, value, report_interval_sec=10):
        return self.Metric(gw, details, value, self, report_interval_sec)

    # TO DO Move metric to one place
    class Metric(object):
        """ Sub-class defined in order to create the metric and publish data
            after the defined report_interval_sec

        """
        def __init__(self, gw, details, sample_function, graphite_obj, report_interval_sec):
            self.gw = gw
            self.details = details
            self.report_interval_sec = report_interval_sec
            self.sample_function = sample_function
            self.graphite_obj = graphite_obj
            log.info("Metrics Created")

        def start_collecting(self):
            """ This function starts the thread in order to collect stats

            """
            message = '%s %s %d\n' % (self.details , self.sample_function(), int(time.time()))
            if self.graphite_obj.sock is not None:
                self.graphite_obj.sock.sendall(message)
                log.info("Publishing value to Graphite DCC for the metric {0}".format(message))
                threading.Timer(self.report_interval_sec, self.start_collecting).start()
            else:
                log.error("DCC Socket Exception")


    def publish(self, sample):
        pass

    def subscribe(self):
        pass
