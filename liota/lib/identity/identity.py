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

from liota.entities.edge_systems.edge_system import EdgeSystem

log = logging.getLogger(__name__)


class RemoteSystemIdentity:
    """
    This encapsulates identity details used to connect to a remote systems both at Dcc and Device side.
        - CA certificate path or Self-signed server certificate path
        - Username-Password combination when authentication is required
    """

    def __init__(self, root_ca_cert, username, password):

        """
        :param root_ca_cert: Root CA certificate path or Self-signed server certificate path
        :param username: Username
        :param password: Corresponding password
        """
        if (root_ca_cert is None) and (username is None or password is None):
            log.error("Either root_ca_cert or username and password must be provided")
            raise ValueError("Either root_ca_cert or username and password must be provided")

        self.root_ca_cert = root_ca_cert
        self.username = username
        self.password = password


class EdgeSystemIdentity:
    """
    This class encapsulates identity details of an Edge System.
        - Edge System's name
        - Client (Edge System) certificate and key file
    """

    def __init__(self, edge_system, cert_file, key_file):

        """
        :param edge_system: EdgeSystem Object
        :param cert_file: Device certificate path
        :param key_file: Device certificate key file
        """
        if not isinstance(edge_system, EdgeSystem):
            log.error("EdgeSystem object is expected.")
            raise TypeError("EdgeSystem object is expected")

        # NOTE:  Only EdgeSystem's name is stored here.
        self.edge_system_name = edge_system.name
        self.cert_file = cert_file
        self.key_file = key_file
