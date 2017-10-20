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
from time import sleep

from liota.lib.utilities.utility import LiotaConfigPath
from liota.lib.utilities.utility import DiscUtilities
from liota.lib.utilities.utility import read_user_config
from liota.dev_sims.named_pipe import NamedPipeSimulator
from liota.dev_sims.socket_clnt import SocketSimulator
from liota.dev_sims.mqtt import MqttSimulator

log = logging.getLogger(__name__)

is_discovery_simulator_initialized = False
# cmd related obj
cmd_message_queue = None
# simulator related obj
simulator_thread = None

DEVICE_TYPE_SAFE_REGEX = '^[A-Za-z0-9_-]+$'

if __name__ == "__main__":
    log.warning("Device Simulator is not supposed to run alone")

    import liota.core.discovery_simulator as actual_discovery_simulator

    log.debug("MainThread is waiting for interruption signal...")
    try:
        while not isinstance(
            actual_discovery_simulator.simulator_thread,
            actual_discovery_simulator.SimulatorThread
        ) or actual_discovery_simulator.simulator_thread.isAlive():
            sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # now only use named pipe for listening manage and statistic cmds
        if actual_discovery_simulator.cmd_message_queue is not None:
            actual_discovery_simulator.cmd_message_queue.put(["terminate"])
    log.info("Exiting Mainthread")
    exit()

class SimulatorThread(Thread):
    """
    SimulatorThread should be instantiated only once.
    Its instance serves core functionalities of Liota device simulator,
    including spawn multiple device simulator beaconing threads, etc.
    """

    def __init__(self, name=None):
        from liota.entities.edge_systems.dell5k_edge_system import Dell5KEdgeSystem

        Thread.__init__(self, name=name)
        # cmd related obj
        self.cmd_messenger_thread = None
        self.cmd_messenger_pipe = None
        # simulator related obj
        self.simulator_lock = None

        # simulator related configuration
        self.endpoint_list = {} # simulator list: (comm type, ip:port or folder)
        self.type_dcc_map = {} # Device Type to DCC mapping: (device type, dcc package name list (e.g., iotcc, iotcc_mqtt))
        self.type_key_map = {} # Device Type to Unique Key mapping: (device type, unique key)
        self.type_tuple_key_dcc_pkg = {} # Device Type to Tuple of (unique key, dcc_pkg)

        self._config = {} #key: cfg type, value: cfg list/info
        self._get_config_from_file() # extract configuration from liota.conf first
        self._executable_check() # check based on configuration, simulator thread is executable or not
        self._save_config()
        # create an edge system instance
        config_path = self._config['package_path']
        config = read_user_config(config_path + '/sampleProp.conf')
        self.edge_system_object = Dell5KEdgeSystem(config['EdgeSystemName'])

        # Initialization of simulator messenger queue and lock
        global cmd_message_queue
        cmd_message_queue = Queue()
        self.simulator_lock = Lock()

        self._simulators = {}  # key: beacon type, value: thread ref
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
                    try:
                        # retrieve simulator cmd pip
                        self.cmd_messenger_pipe = os.path.abspath(
                            config.get('DEVSIM_CFG', 'devsim_cmd_msg_pipe')
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
                                self.simulator_messenger_pipe = os.path.abspath(value)
                                if self.simulator_messenger_pipe is not None:
                                    self.endpoint_list[key] = self.simulator_messenger_pipe
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
        # Will not initialize device simulator if simulator list is empty
        if len(self.endpoint_list) is 0:
            log.error("Device simulator failed because simulator list is empty")
            return

    def _save_config(self):
        # cmd messenger related
        self._config['cmd_msg_pipe'] = self.cmd_messenger_pipe
        # simulator related
        # simulator list: (comm type, ip:port or folder)
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
        # simulator threads
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
        from liota.dev_sims.coap import CoapSimulator

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
                pipe_thread = NamedPipeSimulator(pipe_file=value,
                        name=key+"_Thread", simulator=self)
                if pipe_thread is not None:
                    self._simulators[key] = pipe_thread
            if key.find('socket') != -1:
                if mqtt_only == False:
                    socket_thread = SocketSimulator(ip_port=value,
                            name=key+"_Thread", simulator=self)
                    if socket_thread is not None:
                        self._simulators[key] = socket_thread
                else:
                    log.warning("because security consideration, Socket Endpoint is not allowed!")
                    print "because security consideration, Socket Endpoint is not allowed!"
            if key.find('mqtt') != -1:
                mqtt_thread = MqttSimulator(mqtt_cfg=value,
                        name=key+"_Thread", simulator=self)
                if mqtt_thread is not None:
                    self._simulators[key] = mqtt_thread
            if key.find('coap') != -1:
                if mqtt_only == False:
                    coap_thread = CoapSimulator(ip_port=value,
                            name=key+"_Thread", simulator=self)
                    if coap_thread is not None:
                        self._simulators[key] = coap_thread
                else:
                    log.warning("because security consideration, Coap Endpoint is not allowed!")
                    print "because security consideration, Coap Endpoint is not allowed!"

        # Listen on message queue for management or statistic commands
        global cmd_message_queue
        self.cmd_messenger_thread = \
            CmdMessengerThread(
                pipe_file=self.cmd_messenger_pipe,
                name="CmdMessengerThread",
                cmd_queue = cmd_message_queue
            )
        # currently simulators are only allocated once based on info in liota.conf
        while self.flag_alive:
            msg = cmd_message_queue.get()
            log.info("Got message in cmd messenger queue: %s"
                     % " ".join(msg))
            if not isinstance(msg, tuple) and not isinstance(msg, list):
                raise TypeError(type(msg))

            # Switch on message content (command), determine what to do
            command = msg[0]
            if command == "list":
                with self.simulator_lock:
                    if len(msg) != 2:
                        log.warning("Invalid format of command: %s" % command)
                        continue
                    self._cmd_handler_list(msg[1])
            elif command == "stat":
                with self.simulator_lock:
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
    # simulator, and calls message processor to terminate its threads too.
    # Supposedly, it should be able to let Liota exit elegantly.

    def _terminate_all(self):
        log.info("Shutting down device simulator thread...")
        if (self.cmd_messenger_thread is not None) and (self.cmd_messenger_thread.isAlive()):
            with open(self.cmd_messenger_pipe, "w") as fp:
                fp.write(
                    "terminate_messenger_but_you_should_not_do_this_yourself\n")

        log.info("terminate simulator threads...")
        for k, v in self._simulators.items():
            if v is not None:
                v.clean_up()
                del self._simulators[k]
        return True


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
        global cmd_message_queue
        cmd_message_queue = cmd_queue

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
                        global cmd_message_queue
                        cmd_message_queue.put(msg)
        log.info("Thread exits: %s" % str(self.name))

#---------------------------------------------------------------------------
# Initialization should occur when this module is imported for first time.
# This method create queues and spawns SimulatorThread, which will spins up
# beaconing threads for listed endpoint in liota.conf for simulated devices.

def initialize():
    global is_discovery_simulator_initialized
    if is_discovery_simulator_initialized:
        log.debug("Discovery simulator is already initialized")
        return

    # Initialization of device simulator
    global simulator_thread
    simulator_thread = SimulatorThread(name="SimulatorThread")

    # Mark discovery simulator as initialized
    is_discovery_simulator_initialized = True
    log.info("Device simulator is initialized")

# Initialization of this module
if not is_discovery_simulator_initialized:
    initialize()

log.debug("Discovery simulator is imported")
