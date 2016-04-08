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

from datetime import datetime
import os
import platform
import uuid
import hashlib
import logging
import random

""" Utility functions required for initialization of various objects

"""

log = logging.getLogger(__name__)


class systemUUID:
    __UUID = ''

    def __init__(self):
        if systemUUID.__UUID == '':
            self._set_system_uuid()

    # We decided to explicitly look for interfaces rather than use uuid.getnode() so that
    #    we could support IoT gateways with potentially and only weird interfaces sooner than getnode or netifaces might
    def _getMacAddrIfaceHash(self):
        netifacesExists = ''
        try:
            import netifaces
            netifacesExists = True
        except:
            netifacesExists = False
            log.info('netifaces is not installed, if it were, it would be better')
        mac = '00:00:00:00:00:00'
        if netifacesExists:
            for ifaceName in netifaces.interfaces():
                if netifaces.AF_LINK in netifaces.ifaddresses(ifaceName):
                    mac = netifaces.ifaddresses(ifaceName)[netifaces.AF_LINK][0]['addr']
                    m = hashlib.md5()
                    m.update(mac)
                    m.update(ifaceName)
                    macHash = m.hexdigest()
                    log.info('mac address for interface ' + ifaceName + ' mac=' + str(mac))
                    break
        else:
            if platform.system() == 'Linux':  # netifaces does not exist and this is a Linux variant
                for ifaceName in ['eth0', 'eth1', 'wlan0']:
                    try:
                        mac = open('/sys/class/net/' + ifaceName + '/address').readline()
                        log.info('mac address for interface ' + ifaceName + ' mac=' + str(mac))
                        break
                    except:
                        continue
        if mac == '00:00:00:00:00:00':
            log.warn(
                'could not find a mac address, an unlikely potential exists for uuid collisions with liota instances on other IoT gateways')
            # generate a 48-bit random integer from this seed
            # always returns the same random integer
            # however in get_uuid below a unique uuid for each resource name will be created
            # this allows us not to have to store any uuid on the persistent storage yet
            # create a unique system uuid
            random.seed(1234567)
            mac = str(random.randint(0, 281474976710655))
            ifaceName = 'foobar' #not set above
        m = hashlib.md5()
        m.update(mac)
        m.update(ifaceName)
        self.macHash = m.hexdigest()
        return self.macHash

    def _set_system_uuid(self):
        # start by creating the liota namespace, this is a globally unique uuid, and exactly the same for any instance of liota
        self.liotaNamespace = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/vmware/liota')
        log.info(str('liota namespace uuid: ' + str(self.liotaNamespace)))
        # we create a system uuid for the physical system on which this instance is running
        # we hash the interface name with the mac address in getMacAddrIfaceHash to avoid collision of
        #     mac addresses across potential different physical interfaces in the IoT space
        systemUUID.__UUID = uuid.uuid5(self.liotaNamespace, self._getMacAddrIfaceHash())
        log.info('system UUID: ' + str(systemUUID.__UUID))


    def _get_system_uuid(self):
        if systemUUID.__UUID == '':
            self.set_system_uuid()
        return systemUUID.__UUID


    def get_uuid(self, resource_name):
        # creating a uuid for a particular resource on this system
        # all resources with the same resource name will have the same uuid, on this system
        # resources created on a different system with a name used on this system will have *different* uuids' as it should be
        tmp = str(uuid.uuid5(self._get_system_uuid(), resource_name))
        log.info('resource: ' + resource_name + '  uuid=' + str(tmp))
        return str(tmp)


def get_linux_version():
    return platform.platform()


def getUTCmillis():
    return long(1000 * ((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()))


class findLiotaConfigFullPath:
    __fullPathLiotaConfig = ''
    syswide_path = '/etc/liota/conf/'

    def __init__(self):
        if findLiotaConfigFullPath.__fullPathLiotaConfig == '':
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
                "LIOTA_CONF"), findLiotaConfigFullPath.syswide_path:
            if loc is None:
                continue
            path = os.path.join(loc, 'liota.conf')
            if os.path.exists(path):
                findLiotaConfigFullPath.__fullPathLiotaConfig = path
                break
            else:
                continue
        if findLiotaConfigFullPath.__fullPathLiotaConfig == '':
            print 'liota.conf not found'

    def get_liota_fullpath(self):
        return findLiotaConfigFullPath.__fullPathLiotaConfig
