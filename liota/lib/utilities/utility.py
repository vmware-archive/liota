
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
import hashlib
import logging
import os
import platform
import random
import uuid
import errno
import ConfigParser

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
        # creating a uuid for a particular resource on this system
        # all resources with the same resource name will have the same uuid, on this system
        # resources created on a different system with a name used on this
        # system will have *different* uuids' as it should be
        tmp = str(uuid.uuid5(self._get_system_uuid(), resource_name))
        log.info('resource: ' + resource_name + '  uuid=' + str(tmp))
        return str(tmp)


def get_linux_version():
    return platform.platform()


def getUTCmillis():
    return long(1000 * ((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()))


def mkdir_log(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


def store_edge_system_uuid(entity_name, entity_id, reg_entity_id):
    """
    Utility function to store EdgeSystem's Name, local-uuid and registered-uuid in the
    specified file.
    :param entity_name: EdgeSystem's Name
    :param entity_id: Local uuid of the EdgeSystem
    :param reg_entity_id: Registered uuid of the EdgeSystem
    :return: None
    """
    try:
        uuid_path = read_liota_config('UUID_PATH', 'uuid_path')
        uuid_config = ConfigParser.RawConfigParser()
        uuid_config.optionxform = str
        uuid_config.add_section('GATEWAY')
        uuid_config.set('GATEWAY', 'name', entity_name)
        if entity_id:
            uuid_config.set('GATEWAY', 'local-uuid', entity_id)
        if reg_entity_id:
            uuid_config.set('GATEWAY', 'registered-uuid', reg_entity_id)
        with open(uuid_path, 'w') as configfile:
            uuid_config.write(configfile)
    except ConfigParser.ParsingError, err:
        log.error('Could not open config file ' + str(err))


class LiotaConfigPath:
    path_liota_config = ''
    syswide_path = '/etc/liota/conf/'

    def __init__(self):
        if LiotaConfigPath.path_liota_config == '':
            self._find_path()

    def _find_path(self):
        """ a multi-step search for the configuration file.
        1. Current working directory. ./liota.conf.
        2. User's home directory (~user/liota.conf)
        3. A place named by an environment variable (LIOTA_CONF)
        4. A standard system-wide directory (such as /etc/liota/conf/liota.conf)
        # assert: every install will have a default liota.conf in /etc/liota/conf
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
        return LiotaConfigPath.path_liota_config


def read_liota_config(section, name):
    """Returns the value of name within the specified section.
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


class Credentials:
    """
    This class encapsulates credentials related to a connection  both at Dcc and Device side.
    """

    def __init__(self, root_ca_cert, username, password, cert_file, key_file):
        """
        :param root_ca_cert: Root CA certificate path or Self-signed server certificate path
        :param username: Username
        :param password: Corresponding password
        :param cert_file: Device certificate file path
        :param key_file: Device certificate key-file path
        """
        self.root_ca_cert = root_ca_cert
        self.username = username
        self.password = password
        self.cert_file = cert_file
        self.key_file = key_file


class TLSConf:
    """
    This class encapsulates TLS config related parameters.
    """

    def __init__(self, cert_required, tls_version, cipher):
        """
        :param cert_required: Defines the certificate requirements
        :param tls_version: Version of SSL/TLS protocol to be used
        :param cipher: Ciphers is a string specifying which encryption ciphers are allowable
                        for a connection, or None to use the defaults.
        """
        self.cert_required = cert_required
        self.tls_version = tls_version
        self.cipher = cipher
