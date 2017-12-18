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

""" Utility functions required for initialization of various objects

"""

from datetime import datetime
import ast
import hashlib
import logging
import os
import platform
import random
import uuid
import errno
import ConfigParser
import stat
import json
import subprocess
import time

log = logging.getLogger(__name__)


class systemUUID:
    __UUID = ''

    def __init__(self):
        if systemUUID.__UUID == '':
            self._set_system_uuid()

    # Using uuid.getnode() in order to get the mac address. If all attempts to obtain the hardware address fail, this function returns a random 48-bit number
    # with its eighth bit set to 1 as recommended in RFC 4122. A check on the
    # 8th bit is done in order to figure out if random MAC Address generation
    # is required or not.
    def _getMacAddrIfaceHash(self):
        mac = uuid.getnode()
        if (mac >> 40) % 2:
            # retry after 30 seconds to get the mac address
            # if not able to detect mac address after this try then go ahead with alternate mechanism
            log.info('Retrying getting the mac address')
            time.sleep(30)
            mac = uuid.getnode()
            if (mac >> 40) % 2:
                log.warn(
                    'could not find a mac address, an unlikely potential exists for uuid collisions with liota instances on other IoT gateways')
                # generate a 48-bit random integer from this seed
                # always returns the same random integer
                # however in get_uuid below a unique uuid for each resource name will be created
                # this allows us not to have to store any uuid on the persistent storage yet
                # create a unique system uuid
                random.seed(1234567)
                mac = random.randint(0, 281474976710655)
        m = hashlib.md5()
        m.update(str(mac))
        self.macHash = m.hexdigest()
        return self.macHash

    def _set_system_uuid(self):
        # start by creating the liota namespace, this is a globally unique
        # uuid, and exactly the same for any instance of liota
        self.liotaNamespace = uuid.uuid5(
            uuid.NAMESPACE_URL, 'https://github.com/vmware/liota')
        log.debug(str('liota namespace uuid: ' + str(self.liotaNamespace)))
        # we create a system uuid for the physical system on which this instance is running
        # we hash the interface name with the mac address in getMacAddrIfaceHash to avoid collision of
        # mac addresses across potential different physical interfaces in the
        # IoT space
        systemUUID.__UUID = uuid.uuid5(
            self.liotaNamespace, self._getMacAddrIfaceHash())
        log.debug('system UUID: ' + str(systemUUID.__UUID))

    def _get_system_uuid(self):
        if systemUUID.__UUID == '':
            self._set_system_uuid()
        return systemUUID.__UUID

    def get_uuid(self, resource_name):
        """
        Get/create a uuid for a particular resource on this system.
        All resources with the same resource name will have the same uuid on this system.
        Resources created on a different system with a name used on this
        system will have *different* uuids' as it should be.
        :param resource_name: resource name
        :return: uuid
        """
        tmp = str(uuid.uuid5(self._get_system_uuid(), resource_name.encode('utf-8')))
        log.info('resource: ' + resource_name + '  uuid=' + str(tmp))
        return str(tmp)


def get_linux_version():
    """
    Get linux version.
    :return: linux version
    """
    return platform.platform()


def get_default_network_interface():
    """
    Works with Linux.
    There are situations where route may not actually return a default route in the
    main routing table, as the default route might be kept in another table.
    Such cases should be handled manually.
    :return: Default Network Interface of the Edge_System
    """
    cmd = "route | grep '^default' | grep -o '[^ ]*$'"
    nw_iface = str(subprocess.check_output(cmd, shell=True)).rstrip()
    log.info("Default network interface is : {0}".format(nw_iface))
    return nw_iface


def get_disk_name():
    """
    Works with Linux.
    If edge_system has multiple disks, only first disk will be returned.
    Such cases should be handled manually.

    :return: Disk type of the Edge_System
    """
    cmd = "lsblk -io KNAME,TYPE | grep 'disk' | sed -n '1p' | grep -o '^\S*'"
    disk_name = str(subprocess.check_output(cmd, shell=True)).rstrip()
    log.info("Disk name is : {0}".format(disk_name))
    return disk_name


def getUTCmillis():
    """
    Get UTC now epoch time (since Jan 1, 1970) in milliseconds.
    :return: epoch time in milliseconds
    """
    return long(1000 * ((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()))


def mkdir(path):
    """
    Create a directory if it does not exists.
    :param path: directory path
    :return:
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

def sha1sum(path_file):
    """
    This method calculates SHA-1 checksum of file.
    :param path_file: absolute path of a file
    """
    if not os.path.isfile(path_file):
        return None
    sha1 = hashlib.sha1()
    with open(path_file, "rb") as fp:
        while True:
            data = fp.read(65536)  # buffer size
            if not data:
                break
            sha1.update(data)
    return sha1


class LiotaConfigPath:
    path_liota_config = ''
    syswide_path = '/etc/liota/'

    def __init__(self):
        if LiotaConfigPath.path_liota_config == '':
            self._find_path()

    def _find_path(self):
        """ a multi-step search for the configuration file.
        1. Current working directory. ./liota.conf.
        2. User's home directory (~user/liota.conf)
        3. A place named by an environment variable (LIOTA_CONF)
        4. A standard system-wide directory (such as /etc/liota/liota.conf)
        # assert: every install will have a default liota.conf in /etc/liota/
        """

        for loc in os.curdir, os.path.expanduser("~"), os.environ.get(
                "LIOTA_CONF"), LiotaConfigPath.syswide_path:
            if loc is None:
                continue
            path = os.path.join(loc, 'liota.conf')
            if os.path.exists(path):
                LiotaConfigPath.path_liota_config = path
                break
            else:
                continue
        if LiotaConfigPath.path_liota_config == '':
            log.error('liota.conf file not found')

    def get_liota_fullpath(self):
        """
        Get the full path of liota configuration file.
        :return: configuration file path
        """
        return LiotaConfigPath.path_liota_config

    def setup_logging(self, default_level=logging.WARNING):
        """
        Setup logging configuration
        :param default_level: default message level
        :return:
        """
        log = logging.getLogger(__name__)
        config = ConfigParser.RawConfigParser()
        fullPath = self.get_liota_fullpath()
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
            mkdir(log_path)
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


def read_liota_config(section, name):
    """
    Return the value of name within the specified section.
    :param section: configuration section
    :param name: name of a configuration
    :return: configuration value
    """
    config = ConfigParser.RawConfigParser()
    fullPath = LiotaConfigPath().get_liota_fullpath()
    if fullPath != '':
        try:
            if config.read(fullPath) != []:
                try:
                    value = config.get(section, name)
                except ConfigParser.ParsingError as err:
                    log.error('Could not parse log config file' + str(err))
            else:
                raise IOError('Cannot open configuration file ' + fullPath)
        except IOError as err:
            log.error('Could not open log config file')
    else:
        # missing config file
        log.warn('liota.conf file missing')
    return value


def read_user_config(config_file_path):
    """
    Returns the user defined configuration as a dictionary from DEFAULT section.
    :param config_file_path: path of a configuration file
    :return: the user defined configuration as a dictionary
    """

    config = ConfigParser.RawConfigParser()
    config.optionxform = str
    config.read(config_file_path)

    user_config = dict(config.items('DEFAULT'))
    for key, value in dict(config.items('DEFAULT')).iteritems():
        user_config[key] = ast.literal_eval(value)
    return user_config


class DiscUtilities:
    """
    DiscUtilities is a wrapper of utility functions
    """

    def __init__(self):
        pass

    def validate_named_pipe(self, pipe_file):
        """
        Check whether a named pipe exists: if not, create it and set permission.
        :param pipe_file: path of a named pipe file
        :return: True or False (named pipe finally exists or not)
        """

        assert (isinstance(pipe_file, basestring))
        if os.path.exists(pipe_file):
            if stat.S_ISFIFO(os.stat(pipe_file).st_mode):
                pass
            else:
                log.error("Pipe path exists, but it is not a pipe")
                return False
        else:
            pipe_dir = os.path.dirname(pipe_file)
            if not os.path.isdir(pipe_dir):
                try:
                    os.makedirs(pipe_dir)
                    log.info("Created directory: " + pipe_dir)
                except OSError:
                    log.error("Could not create directory for messenger pipe")
                    return False
            try:
                os.mkfifo(pipe_file, 0600)
                log.info("Created pipe: " + pipe_file)
            except OSError:
                log.error("Could not create messenger pipe")
                return False
        assert (stat.S_ISFIFO(os.stat(pipe_file).st_mode))
        return True
