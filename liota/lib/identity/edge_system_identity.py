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


class Identity:
    """
    This class encapsulates identity details of an Edge System :
        - Edge System's name
        - CA certificate
        - Client (Edge System) certificate and key file
        - Username-Password combination when authentication is required
    """

    def __init__(self, edge_system, ca_cert, cert_file, key_file, username, password):

        """
        :param edge_system: EdgeSystem Object
        :param ca_cert: CA Certificate path
        :param cert_file: Device certificate path
        :param key_file: Device certificate's key file
        :param username: Username
        :param password: Password
        """
        if not isinstance(edge_system, EdgeSystem):
            raise TypeError("EdgeSystem object is expected")

        if cert_file and key_file:
            if not ca_cert:
                raise ValueError("CA certificate path is required, when certification based auth is used")

        if (cert_file is None or key_file is None) and (username is None or password is None):
            raise ValueError("Either cert_file and key_file path or username and password must be provided")

        # NOTE:  Only EdgeSystem's name is stored here.
        self.edge_system_name = edge_system.name
        self.ca_cert = ca_cert
        self.cert_file = cert_file
        self.key_file = key_file
        self.username = username
        self.password = password
