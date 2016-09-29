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

import ConfigParser
import errno
import json
import logging
import logging.config
import os

from lib.utilities.utility import systemUUID, LiotaConfigPath, mkdir_log


def setup_logging(default_level=logging.WARNING):
    """Setup logging configuration

    """
    log = logging.getLogger(__name__)
    config = ConfigParser.RawConfigParser()
    fullPath = LiotaConfigPath().get_liota_fullpath()
    if fullPath != '':
        try:
            if config.read(fullPath) != []:
                # now use json file for logging settings
                try:
                    log_path = config.get('LOG_PATH', 'log_path')
                    log_cfg = config.get('LOG_CFG', 'json_path')
                except ConfigParser.ParsingError as err:
                    log.error('Could not parse log config file')
            else:
                raise IOError('Cannot open configuration file ' + fullPath)
        except IOError as err:
            log.error('Could not open log config file')
        mkdir_log(log_path)
        if os.path.exists(log_cfg):
            with open(log_cfg, 'rt') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
            log.info('created logger with ' + log_cfg)
        else:
            # missing logging.json file
            logging.basicConfig(level=default_level)
            log.warn(
                'logging.json file missing,created default logger with level = ' +
                str(default_level))
    else:
        # missing config file
        log.warn('liota.conf file missing')

setup_logging()
systemUUID()
