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
import os
import re
import fcntl
import errno
import ConfigParser
from threading import Thread, Lock
from Queue import Queue

from liota.lib.utilities.utility import LiotaConfigPath, DiscUtilities
from liota.disc_listeners.named_pipe import NamedPipeListener
from liota.disc_listeners.socket_svr import SocketListener
from liota.disc_listeners.mqtt import MqttListener

log = logging.getLogger(__name__)

DEVICE_TYPE_SAFE_REGEX = '^[A-Za-z0-9_-]+$'
DEVICE_KEY_SAFE_REGEX = '^[A-Za-z0-9_-]+$'
DEVICE_VAL_SAFE_REGEX = '^[A-Za-z0-9\._-]+$'

class DiscoveryThread(Thread):
    """
    DiscoveryThread should be instantiated only once.
    Its instance serves core functionalities of Liota device discovery,
    including spawn multiple discovery listening threads,
    maintenance of discovered device records, etc.
    """

    def __init__(self, name=None, registry=None):
        Thread.__init__(self, name=name)
        # cmd related obj
        self.cmd_message_queue = None
        self.cmd_messenger_thread = None
        self.cmd_messenger_pipe = None
        # discovery related obj
        self.discovery_lock = None

        # listener related configuration
        self.endpoint_list = {} # Listener list: (comm type, ip:port or folder)
        self.type_dcc_map = {} # Device Type to DCC mapping: (device type, dcc package name list (e.g., iotcc, iotcc_mqtt))
        self.type_key_map = {} # Device Type to Unique Key mapping: (device type, unique key)
        self.type_tuple_key_dcc_pkg = {} # Device Type to Tuple of (unique key,  dcc_pkg)

        # device registration to dcc related
        self.pkg_registry = registry
        self.package_path = self.pkg_registry.get("package_conf")
        self.dev_file_path = None

        self._config = {} #key: cfg type, value: cfg list/info
        self._get_config_from_file() # extract configuration from liota.conf first
        self._executable_check() # check based on configuration, discovery thread is executable or not
        self._save_config()

        # Initialization of device discovery messenger queue and lock
        self.cmd_message_queue = Queue()
        self.discovery_lock = Lock()

        self._listeners = {}  # key: listen type, value: thread ref
        self._devices_discoverd = {}  # key: device name, value: device obj
        self.flag_alive = True
        self.start()

    def _get_config_from_file(self):
        # Parse Liota configuration file
        config = ConfigParser.RawConfigParser()
        config.optionxform=str
        fullPath = LiotaConfigPath().get_liota_fullpath()
        if fullPath != '':
            try:
                if config.read(fullPath) != []:
                    try:
                        # retrieve device info file storage directory
                        self.dev_file_path = config.get('IOTCC_PATH', 'dev_file_path')
                        # retrieve organization info file storage directory
                        self.org_file_path = config.get('IOTCC_PATH', 'iotcc_path')
                    except ConfigParser.ParsingError as err:
                        log.error('Could not parse log config file' + err)
                        exit(-4)
                    if not os.path.exists(self.dev_file_path):
                        try:
                            os.makedirs(self.dev_file_path)
                        except OSError as exc:  # Python >2.5
                            if exc.errno == errno.EEXIST and os.path.isdir(self.dev_file_path):
                                pass
                            else:
                                log.error('Could not create device file storage directory')
                                exit(-4)
                    if not os.path.exists(self.org_file_path):
                        log.error('No organization info file (iotcc.json)')
                    try:
                        # retrieve discovery cmd pip
                        self.cmd_messenger_pipe = os.path.abspath(
                            config.get('DISC_CFG', 'disc_cmd_msg_pipe')
                        )
                        # retrieve package path (later use config file to register device)
                        self.package_path = os.path.abspath(
                            config.get('PKG_CFG', 'pkg_path')
                        )
                        # retrieve endpoint list
                        tmp_list = config.items('DISC_ENDPOINT_LIST')
                        for key, value in tmp_list[:]:
                            if value is None or value == "None":
                                continue
                            if key.find('disc_msg_pipe') != -1:
                                self.discovery_messenger_pipe = os.path.abspath(value)
                                if self.discovery_messenger_pipe is not None:
                                    self.endpoint_list[key] = self.discovery_messenger_pipe
                            elif key.find('socket') != -1:
                                self.endpoint_list[key] = value
                            elif key.find('mqtt') != -1:
                                # retrieve mqtt configurations
                                mqtt_cfg_dict = dict(config.items('DISC_MQTT_CFG'))
                                # make broker_ip:port:topic included inside mqtt_cfg_dict
                                mqtt_cfg_dict["broker_ip_port_topic"] = value
                                self.endpoint_list[key] = mqtt_cfg_dict
                            elif key.find('coap') != -1:
                                self.endpoint_list[key] = value
                            else:
                                log.error(key + ' is currently not supported!')
                        for key in self.endpoint_list.iterkeys():
                            log.debug("endpoint_list:(%s : %s)\n" % (key, self.endpoint_list[key]))

                        global DEVICE_TYPE_SAFE_REGEX
                        # retrieve device type to unique key mapping list
                        tmp_list = config.items('DEVICE_TYPE_TO_UNIQUEKEY_MAPPING')
                        for key, value in tmp_list[:]:
                            if not re.match(DEVICE_TYPE_SAFE_REGEX, key):
                                log.warning("device type {0} contains unacceptable character".format(key))
                                continue
                            if value is None or value == "None":
                                continue
                            self.type_key_map[key] = value
                        for key in self.type_key_map.iterkeys():
                            log.debug("type_key_map:(%s : %s)\n" % (key, self.type_key_map[key]))

                        # retrieve device type to DCC mapping list
                        tmp_list = config.items('DEVICE_TYPE_TO_DCC_MAPPING')
                        for key, value in tmp_list[:]:
                            if not re.match(DEVICE_TYPE_SAFE_REGEX, key):
                                log.warning("device type {0} contains unacceptable character".format(key))
                                continue
                            if value is None or value == "None":
                                continue
                            tmp_list2 = []
                            tmp_list2 = [x.strip() for x in value.split(',')]
                            self.type_dcc_map[key] = tmp_list2
                            self.type_tuple_key_dcc_pkg[key] = (self.type_key_map[key], tmp_list2)
                        for key in self.type_dcc_map.iterkeys():
                            log.debug("type_dcc_map:(%s : %s)\n" % (key, self.type_dcc_map[key]))
                        for key in self.type_tuple_key_dcc_pkg.iterkeys():
                            log.debug("type_tuple_key_dcc_pkg:(%s : %s)\n" % (key, self.type_tuple_key_dcc_pkg[key]))
                    except ConfigParser.ParsingError:
                        log.error('Could not parse log config file')
                        exit(-4)
                else:
                    raise IOError('Could not open configuration file: ' + fullPath)
            except IOError:
                raise IOError('Could not open configuration file: ' + fullPath)
        else:
            # missing config file
            log.error('liota.conf file missing')

        assert(isinstance(self.cmd_messenger_pipe, basestring))

    def _executable_check(self):
        if DiscUtilities().validate_named_pipe(self.cmd_messenger_pipe) == False:
            return None
        # Will not initialize device discovery if DISCOVERY_LISTENER list is empty
        if len(self.endpoint_list) is 0:
            log.error("Device discovery failed because listener list is empty")
            return
        # later needed when register device
        if self.pkg_registry is None:
            log.error("Device discovery failed because no package manager's registry info")
            return

    def _save_config(self):
        # cmd messenger related
        self._config['cmd_msg_pipe'] = self.cmd_messenger_pipe
        # listen related
        # Listener list: (comm type, ip:port or folder)
        self._config['endpoint_list'] = self.endpoint_list
        # Device Type to DCC mapping: (device type, dcc package name list (e.g., iotcc, iotcc_mqtt))
        self._config['type_dcc_map'] = self.type_dcc_map
        # Device Type to Unique Key mapping: (device type, unique key)
        self._config['type_key_map'] = self.type_key_map
        # Device Type to Tuple of (unique key, dcc, dcc_pkg)
        self._config['type_tuple_key_dcc_pkg'] = self.type_tuple_key_dcc_pkg
        # package path
        self._config['package_path'] = self.package_path
        # device info storage path
        self._config['dev_file_path']= self.dev_file_path
        # organization (edgesystem+devices) info storage path
        self._config['org_file_path']= self.org_file_path

    #-----------------------------------------------------------------------
    # This method is used to handle listing commands

    def _cmd_handler_list(self, parameter):
        # configurations
        if parameter == "configurations" or parameter == "cfg":
            stats = ["n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]
            stats[0] = str(self._config['cmd_msg_pipe']) + '\n\t'
            tmp = ''
            endpoint_list = self._config['endpoint_list']
            for key in endpoint_list.iterkeys():
                tmp += str(key) + ': ' + str(endpoint_list[key]) + '\n\t\t'
            stats[1] = tmp

            tmp = ''
            type_dcc_map = self._config['type_dcc_map']
            for key in type_dcc_map.iterkeys():
                tmp += str(key) + ': ' + str(type_dcc_map[key]) + '\n\t\t'
            stats[2] = tmp

            tmp = ''
            type_key_map = self._config['type_key_map']
            for key in type_key_map.iterkeys():
                tmp += str(key) + ': ' + str(type_key_map[key]) + '\n\t\t'
            stats[3] = tmp

            tmp = ''
            type_tuple_key_dcc_pkg = self._config['type_tuple_key_dcc_pkg']
            for key in type_tuple_key_dcc_pkg.iterkeys():
                tmp += str(key) + ': ' + str(type_tuple_key_dcc_pkg[key]) + '\n\t\t'
            stats[4] = tmp

            stats[5] = str(self._config['package_path']) + '\n\t'
            stats[6] = str(self._config['dev_file_path']) + '\n\t'
            log.warning(("List of configurations - \t"
                        + "cmd_msg_pipe: %s\t"
                        + "endpoint_list: %s\t"
                        + "type_dcc_map: %s\t"
                        + "type_key_map: %s\t"
                        + "type_tuple_key_dcc_pkg: %s\t"
                        + "dev_file_path: %s\t"
                        + "package_path: %s"
                        ) % tuple(stats))
            return
        # discovered devices
        if parameter == "devices" or parameter == "dev":
            log.warning("List of devices - \t%s"
                        % "\t".join(sorted(
                            self._devices_discoverd.keys()
                        ))
                        )
            return
        # registered devices
        if parameter == "resources" or parameter == "res":
            log.warning("List of resources - \t%s"
                    % "\n\t".join(
                        ['Device Name: %s\t Type: %s\t Reg_info: %s' %
                        (key, self._devices_discoverd[key][0], self._devices_discoverd[key][1])
                        for key in self._devices_discoverd.iterkeys()]
                        )
                    )
            return
        # listening threads
        if parameter == "threads" or parameter == "th":
            import threading

            log.warning("Active threads - \t%s"
                        % "\t".join(map(
                            lambda tref: "%s: %016x %s %s" % (
                                tref.name,
                                tref.ident,
                                type(tref).__name__.split(".")[-1],
                                tref.isAlive()
                            ),
                            sorted(
                                threading.enumerate(),
                                key=lambda tref: tref.ident
                            )
                        ))
                        )
            return
        log.warning("Unsupported list")

    #-----------------------------------------------------------------------
    # This method is used to handle statistical commands

    def _cmd_handler_stat(self, parameter):
        if parameter == "threads" or parameter == "th":
            import threading

            log.warning("Count of active threads: %d"
                        % threading.active_count())
            return
        log.warning("Unsupported stat")

    #-----------------------------------------------------------------------
    # This method will loop on message queue and select methods to call with
    # respect to commands received.

    def run(self):
        from liota.disc_listeners.coap import CoapListener

        endpoint_list = self._config['endpoint_list']

        # spin listening threads according to endpoint_list extracted config
        for key in endpoint_list.iterkeys():
            value = endpoint_list[key]
            log.debug("Endpoint:{0}:{1}".format(key, value))
            if value is None or value == "None":
                continue
            ### TBR: because security consideration, currently only mqtt is allowed
            mqtt_only = True
            if key.find('disc_msg_pipe') != -1:
                pipe_thread = NamedPipeListener(pipe_file=value, name=key+"_Thread", discovery=self)
                if pipe_thread is not None:
                    self._listeners[key] = pipe_thread
            if key.find('socket') != -1:
                if mqtt_only == False:
                    socket_thread = SocketListener(ip_port=value, name=key+"_Thread", discovery=self)
                    if socket_thread is not None:
                        self._listeners[key] = socket_thread
                else:
                    log.warning("because security consideration, Socket Endpoint is not allowed!")
                    print "because security consideration, Socket Endpoint is not allowed!"
            if key.find('mqtt') != -1:
                mqtt_thread = MqttListener(mqtt_cfg=value, name=key+"_Thread", discovery=self)
                if mqtt_thread is not None:
                    self._listeners[key] = mqtt_thread
            if key.find('coap') != -1:
                if mqtt_only == False:
                    coap_thread = CoapListener(ip_port=value, name=key+"_Thread", discovery=self)
                    if coap_thread is not None:
                        self._listeners[key] = coap_thread
                else:
                    log.warning("because security consideration, Coap Endpoint is not allowed!")
                    print "because security consideration, Coap Endpoint is not allowed!"

        # Listen on message queue for management or statistic commands
        self.cmd_messenger_thread = \
            CmdMessengerThread(
                pipe_file=self.cmd_messenger_pipe,
                name="CmdMessengerThread",
                cmd_queue = self.cmd_message_queue
            )

        # currently listeners are only allocated once based on info in liota.conf
        while self.flag_alive:
            msg = self.cmd_message_queue.get()
            log.info("Got message in cmd messenger queue: %s"
                     % " ".join(msg))
            if not isinstance(msg, tuple) and not isinstance(msg, list):
                raise TypeError(type(msg))

            # Switch on message content (command), determine what to do
            command = msg[0]
            if command == "list":
                with self.discovery_lock:
                    if len(msg) != 2:
                        log.warning("Invalid format of command: %s" % command)
                        continue
                    self._cmd_handler_list(msg[1])
            elif command == "stat":
                with self.discovery_lock:
                    if len(msg) != 2:
                        log.warning("Invalid format of command: %s" % command)
                        continue
                    self._cmd_handler_stat(msg[1])
            elif command == "terminate":
                if self._terminate_all():
                    self.flag_alive = False
                    break
            else:
                log.warning("Unsupported command is dropped")

        log.info("Thread exits: %s" % str(self.name))

    #-----------------------------------------------------------------------
    # This method is called to signal termination to all threads in device
    # discovery, and calls message processor to terminate its threads too.
    # Supposedly, it should be able to let Liota exit elegantly.

    def _terminate_all(self):
        log.info("Shutting down device discovery thread...")
        if (self.cmd_messenger_thread is not None) and (self.cmd_messenger_thread.isAlive()):
            with open(self.cmd_messenger_pipe, "w") as fp:
                fp.write(
                    "terminate_messenger_but_you_should_not_do_this_yourself\n")

        log.info("terminate listening threads...")
        for k, v in self._listeners.items():
            if v is not None:
                v.clean_up()
                del self._listeners[k]
        return True

    #-----------------------------------------------------------------------
    # Record discovered device and register info
    # key: device name, tuple (dev_type, dev info list); list: (dcc, dev_)
    def _save_devinfo(self, name, dev_type):
        # initialization
        with self.discovery_lock:
            self._devices_discoverd[name] = (dev_type, [])

    def _update_devinfo(self, name, reg_rec):
        with self.discovery_lock:
            dev_type = self._devices_discoverd[name][0]
            reg_list = self._devices_discoverd[name][1]
            reg_list.append(reg_rec)
            self._devices_discoverd[name] = (dev_type, reg_list)

    def add_organization_properties(self, key, prop_dict):
        import json

        # Get organization info file path
        iotcc_json_path = self._config['org_file_path']
        if iotcc_json_path == '':
            return prop_dict
        try:
            with open(iotcc_json_path, 'r') as f:
                iotcc_details_json_obj = json.load(f)[key]
            f.close()
        except IOError, err:
            return prop_dict

        org_group_properties = iotcc_details_json_obj["OGProperties"]
        # merge org properties into prop_dict
        new_prop_dict = dict(prop_dict.items() + org_group_properties.items())
        return new_prop_dict

    def reg_device(self, dcc_pkg, edge_system_pkg, name, dev_type, prop_dict):
        from liota.entities.devices.device import Device
        from liota.lib.utilities.utility import systemUUID

        # Acquire resources from registry
        if not self.pkg_registry.has(dcc_pkg):
            log.warning("%s package is not running" % dcc_pkg)
            return None, None
        dcc = self.pkg_registry.get(dcc_pkg)

        dev = Device(name, systemUUID().get_uuid(name), dev_type)
        # Register device
        try:
            with self.discovery_lock:
                reg_dev = dcc.register(dev)
                dcc.set_properties(reg_dev, prop_dict)
        except:
            return None, None

        # TBM: temporarily assume devices will be attached to the only edge system
        if self.pkg_registry.has(edge_system_pkg):
            edge_system = self.pkg_registry.get(edge_system_pkg)
            dcc.create_relationship(edge_system, reg_dev)
        else:
            log.warning("%s package is not loaded, please load it!" % edge_system_pkg)
        return dev, reg_dev

    def device_msg_process(self, data):
        """
        process json messages received by listeners.
        msg format is {'DeviceType':{key1:value1,key2:value2, …, keyn:valuen}},
        where UniqueKey is defined in liota.conf, ie.,
        """

        log.debug("device_msg_process")
        type_dcc_map = self._config['type_dcc_map']
        type_key_map = self._config['type_key_map']
        for key in type_dcc_map.iterkeys():
            log.debug("type_dcc_map:(%s : %s)\n" % (key, type_dcc_map[key]))

        global DEVICE_TYPE_SAFE_REGEX
        global DEVICE_KEY_SAFE_REGEX
        global DEVICE_VAL_SAFE_REGEX
        try:
            for key, value in data.iteritems():
                if not re.match(DEVICE_TYPE_SAFE_REGEX, key):
                    log.warning("device type {0} contains unacceptable character".format(key))
                    return False
                key_dcc = type_dcc_map.get(key)
                if key_dcc is None:
                    continue
                if len(key_dcc) is 0:
                    continue
                unique_key = type_key_map.get(key)
                if unique_key is None:
                    continue
                unique_key_value = ''
                for k, v in value.iteritems():
                    if not re.match(DEVICE_KEY_SAFE_REGEX, k):
                        log.warning("Property key {0} contains unacceptable character".format(k))
                        return False
                    if not re.match(DEVICE_VAL_SAFE_REGEX, v):
                        log.warning("Property value {0} contains unacceptable character".format(v))
                        return False
                    if k == unique_key:
                        unique_key_value = v
                name = key + '_' + unique_key_value;
                self._save_devinfo(name, key)
                for dcc in key_dcc[:]:
                    # register device to dcc, set properties for the device
                    if 'iotcc' in dcc.lower():
                        prop_dict = self.add_organization_properties("iotcc", value)
                    else:
                        prop_dict = value
                    # TBM: temporarily assume dcc pkg will register edge_system as dcc name + "_edge_system"
                    edge_system_pkg = dcc + str("_edge_system")
                    (dev, reg_dev) = self.reg_device(dcc, edge_system_pkg, name, key, prop_dict)
                    if (dev is not None) and (reg_dev is not None):
                        reg_rec = {}
                        # add it in Records: currently only for debugging
                        reg_rec[dcc] = (dev, reg_dev)
                        self._update_devinfo(name, reg_rec)
        except:
            log.exception("device_msg_process exception")

class CmdMessengerThread(Thread):
    """
    CmdMessengerThread does inter-process communication (IPC) to listen
    to commands casted by other processes.
    Current implementation of CmdMessengerThread blocks on a named pipe.
    """

    def __init__(self, pipe_file, name=None, cmd_queue=None):
        Thread.__init__(self, name=name)
        self._pipe_file = pipe_file
        if cmd_queue is None:
            log.error("Thread exits: %s (because cmd_queue is None)" % str(self.name))
            return
        self.cmd_message_queue = cmd_queue

        # Unblock previous writers
        BUFFER_SIZE = 65536
        ph = None
        try:
            ph = os.open(self._pipe_file, os.O_RDONLY | os.O_NONBLOCK)
            flags = fcntl.fcntl(ph, fcntl.F_GETFL)
            flags &= ~os.O_NONBLOCK
            fcntl.fcntl(ph, fcntl.F_SETFL, flags)
            while True:
                buf = os.read(ph, BUFFER_SIZE)
                if not buf:
                    break
        except OSError as err:
            if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
                pass  # It is supposed to raise one of these exceptions
            else:
                raise err
        finally:
            if ph:
                os.close(ph)

        self.flag_alive = True
        self.start()

    def run(self):

        while self.flag_alive:
            with open(self._pipe_file, "r") as fp:
                for line in fp.readlines():
                    msg = line.split()
                    if len(msg) > 0:
                        if len(msg) == 1 and msg[0] == \
                                "terminate_messenger_but_you_should_not_do_this_yourself":
                            self.flag_alive = False
                            break
                        self.cmd_message_queue.put(msg)
        log.info("Thread exits: %s" % str(self.name))