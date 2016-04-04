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

# package/__init__.py
import json
import logging
import logging.config
import os
import time
import ConfigParser

syswide_path = "/etc/liota/conf/"

def read_log_cfg(path):
    """ a multi-step search for the configuration file.
    1. Local directory. ./liota.conf.
    2. User's home directory (~user/liota.conf)
    3. A standard system-wide directory (such as /etc/liota/conf/liota.conf)
    4. A place named by an environment variable (LIOTA_CONF)
    """
    log_cfg = None
    config = ConfigParser.RawConfigParser()
    for loc in os.curdir, os.path.expanduser("~"), syswide_path, os.environ.get("LIOTA_CONF"):
        if loc is None:
            continue
        path = os.path.join(loc,"liota.conf")
        print path
        try:
            if config.read(path) != []:
                # now use json file for logging settings
                try:
                    log_cfg = config.get('LOG_CFG', 'json_path')
                    print log_cfg
                    break
                except ConfigParser.ParsingError, err:
                    print 'Could not parse:', err
            else:
                raise IOError('Cannot open configuration file ' + path)
        except IOError, err:
            print 'Could not open:', err
    return log_cfg

def setup_logging(
    default_path='../config/logging.json',
    default_level=logging.WARNING,
):
    """Setup logging configuration

    """
    path = default_path
    value = read_log_cfg(syswide_path)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

setup_logging()
