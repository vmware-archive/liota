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
import imp
import os
import fcntl
import stat
import re
from threading import Thread, Lock
from Queue import Queue
from time import sleep
from abc import ABCMeta, abstractmethod

from liota.lib.utilities.utility import read_liota_config, sha1sum

log = logging.getLogger(__name__)

if __name__ == "__main__":
    log.warning("Package manager is not supposed to run alone")

    import liota.core.package_manager as actual_package_manager

    log.debug("MainThread is waiting for interruption signal...")
    try:
        while not isinstance(
            actual_package_manager.package_thread,
            actual_package_manager.PackageThread
        ) or actual_package_manager.package_thread.isAlive():
            sleep(1)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        if actual_package_manager.package_message_queue is not None:
            actual_package_manager.package_message_queue.put(["terminate"])
    log.info("Exiting Mainthread")
    exit()

is_package_manager_initialized = False

package_message_queue = None
package_messenger_thread = None
package_thread = None
package_lock = None
package_path = None
package_messenger_pipe = None

# Parse Liota configuration file
package_path = os.path.abspath(
    read_liota_config('PKG_CFG', 'pkg_path')
)
package_messenger_pipe = os.path.abspath(
    read_liota_config('PKG_CFG', 'pkg_msg_pipe')
)
assert(isinstance(package_path, basestring))
assert(isinstance(package_messenger_pipe, basestring))

package_startup_list_path = None
package_startup_list = []

# Parse packages to load at start-up
package_startup_list_path = os.path.abspath(
    read_liota_config('PKG_CFG', 'pkg_list')
)

class ResourceRegistryPerPackage:
    """
    ResourceRegistryPerPackage creates temporary objects for packages while
    loading, so when they register their resource refs, we can keep track of
    them in resource registry and automatically remove them later when these
    packages are unloaded.
    """

    def __init__(self, outer, package_name):
        self._outer = outer
        self._package_name = package_name

    def register(self, identifier, ref):
        """
        Store resource/object reference with certain name/identifier
        for the package.
        :param identifier: identifier for resource reference (ref)
        :param ref: reference for a resource
        :return:
        """
        self._outer.register(identifier, ref, self._package_name)

    def get(self, identifier):
        """
        Get resource/object reference by a name/identifier.
        :param identifier: identifier for a registered resource
        :return: resource reference
        """
        return self._outer.get(identifier)

    def has(self, identifier):
        """
        Check whether a resource has been registered with an identifier or not.
        :param identifier: identifier for a resource
        :return: True or False
        """
        return self._outer.has(identifier)


class ResourceRegistry:
    """
    ResourceRegistry is a wrapped structure for Liota packages to register
    resources and find resources registered by other packages.
    """

    def __init__(self):
        self._registry = {}  # key: resource name, value: resource ref
        self._packages = {}  # key: package name, value: list of resource names

    def register(self, identifier, ref, package_name=None):
        """
        Store resource/object reference with certain name/identifier
        for a package with certain name.
        :param identifier: identifier for resource reference (ref)
        :param ref: reference for a resource
        :param package_name: the name of a package to register a resource to
        :return:
        """
        if identifier in self._registry:
            raise KeyError("Conflicting resource identifier: " + identifier)
        self._registry[identifier] = ref
        if package_name:
            if package_name not in self._packages:
                self._packages[package_name] = []
            self._packages[package_name].append(identifier)

    def deregister(self, identifier):
        """
        Remove the record of a resource with a name/identifier.
        :param identifier: identifier for a resource
        :return:
        """
        del self._registry[identifier]

    def get(self, identifier):
        """
        Get resource/object reference by a name/identifier.
        :param identifier: identifier for a registered resource
        :return: resource reference
        """
        return self._registry[identifier]

    def has(self, identifier):
        """
        Check whether a resource has been registered with an identifier or not.
        :param identifier: identifier for a resource
        :return: True or False
        """
        return identifier in self._registry

    #-----------------------------------------------------------------------
    # This method generate a package specific registry object, so when they
    # register their resource refs, we keep track of them and can deregister
    # them automatically if package is unloaded.

    def get_package_registry(self, package_name):
        """
        Get the instance of ResourceRegistryPerPackage by package name.
        :param package_name: the name of a package
        :return: the reference of a ResourceRegistryPerPackage instance
        """
        return ResourceRegistryPerPackage(self, package_name)


class LiotaPackage:
    """
    LiotaPackage is ABC (abstract base class) of all package classes.
    Developers should extend LiotaPackage class and implement the abstract methods.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self, registry):
        """
        The execution function of a liota package.
        :param registry: the instance of ResourceRegistryPerPackage of the package
        """
        raise NotImplementedError

    @abstractmethod
    def clean_up(self):
        """
        The clean up function of a liota package.
        """
        raise NotImplementedError


class PackageRecord:
    """
    PackageRecord is instantiated for each package loaded.
    It contains necessary information of packages, including but may not be
    limited to file names, checksums, and refs to package class instances.
    These records make it possible to start and stop package class instances
    elegantly.
    """

    def __init__(self, file_name):
        self._file_name = file_name
        self._ext = None
        self._sha1 = None
        self._dependents = {}  # key: dependent name, value: None
        self._dependencies = []

        #-------------------------------------------------------------------
        # To guarantee successful garbage collection when record is removed,
        # this should be the ONLY variable to keep its reference.

        self._instance = None

    def set_instance(self, obj):
        """
        Set _instance field for an instance of PackageRecord of a liota package.
        :param obj: a liota package class instance
        :return: True or False
        """
        if self._instance is not None:
            log.warning("Should not override instance of package class")
            return False
        self._instance = obj
        return True

    def get_instance(self):
        """
        Set the instance of a liota package class.
        :return: the reference of a liota package class instance
        """
        return self._instance

    def set_sha1(self, sha1):
        """
        Set _sha1 field for an instance of PackageRecord of a liota package.
        :param sha1: the SHA-1 checksum of a liota package
        :return:
        """
        self._sha1 = sha1

    def get_sha1(self):
        """
        Get the SHA-1 checksum of a liota package.
        :return: the SHA-1 checksum of a liota package
        """
        return self._sha1

    def set_ext(self, ext):
        """
        Set _ext field for an instance of PackageRecord.
        :param ext: the extention of a liota package file
        :return:
        """
        self._ext = ext

    def get_ext(self):
        """
        Get the extention of a liota package file.
        :return: the extention of a liota package file
        """
        return self._ext

    def get_dependents(self):
        """
        Get dependent package names of a liota package.
        :return: the dependent package names of a liota package
        """
        return self._dependents.keys()

    def add_dependent(self, file_name):
        """
        Add the record for a package into dependent dictionary.
        :param file_name: the name of a liota package file
        :return:
        """
        self._dependents[file_name] = None

    def del_dependent(self, file_name):
        """
        Delete the record for a package from dependent dictionary.
        :param file_name: the name of a liota package file
        :return:
        """
        del self._dependents[file_name]

    def get_dependencies(self):
        """
        Get the dependency list of the liota package.
        :return: the dependency list of the liota package
        """
        return self._dependencies

    def set_dependencies(self, list_dependencies):
        """
        Set the dependency list for the liota package.
        :param list_dependencies: the dependency list of the liota package
        :return:
        """
        self._dependencies = list_dependencies


class PackageThread(Thread):
    """
    PackageThread should be instantiated only once.
    Its instance serves core functionalities of Liota package manager,
    including load/unload of packages, maintenance of loaded package records,
    etc.
    """

    def __init__(self, name=None):
        Thread.__init__(self, name=name)

        global package_path

        self._packages_loaded = {}  # key: package name, value: PackageRecord obj
        self._resource_registry = ResourceRegistry()
        self._resource_registry.register("package_conf", package_path)
        self.flag_alive = True
        self.start()

    #-----------------------------------------------------------------------
    # This method is used to handle listing commands

    def _cmd_handler_list(self, parameter):
        if parameter == "packages" or parameter == "pkg":
            log.warning("List of packages - \t%s"
                        % "\t".join(sorted(
                            self._packages_loaded.keys()
                        ))
                        )
            return
        if parameter == "resources" or parameter == "res":
            log.warning("List of resources - \t%s"
                        % "\t".join(sorted(
                            self._resource_registry._registry.keys()
                        ))
                        )
            return
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

    def _cmd_handler_stat(self, parameters):
        if parameters[0] == "package" or parameters[0] == "pkg":
            if (len(parameters) < 2):
                log.warning("package name is not specified")
                return
            if (len(parameters) > 2):
                log.warning("Only 1 package name will be taken and processed")
            query_pkg = parameters[1]
            if query_pkg in self._packages_loaded.keys():
                log.info("packages {0} is loaded".format(query_pkg))
            else:
                log.info("packages {0} is not loaded".format(query_pkg))
            return
        if len(parameters) != 1:
            log.warning("Invalid format of stat command: %s" % parameters[0])
            return
        if parameters[0] == "metrics" or parameters[0] == "met":
            from liota.core.metric_handler \
                import event_ds, collect_queue, send_queue, \
                CollectionThreadPool, collect_thread_pool

            stats = ["n/a", "n/a", "n/a", "n/a"]
            if isinstance(event_ds, Queue):
                stats[0] = str(event_ds.qsize())
            if isinstance(send_queue, Queue):
                stats[1] = str(send_queue.qsize())
            if isinstance(collect_queue, Queue):
                stats[2] = str(collect_queue.qsize())
            if isinstance(collect_thread_pool, CollectionThreadPool):
                stats[3] = collect_thread_pool.get_stats_working()[0]
            log.warning(("Number of metrics in - \t"
                         + "Waiting queue: %s\t"
                         + "Sending queue: %s\t"
                         + "Collecting queue: %s\t"
                         + "Collecting threads: %s"
                         ) % tuple(stats))
            return
        if parameters[0] == "collection_threads" or parameters[0] == "col":
            from liota.core.metric_handler \
                import CollectionThreadPool, collect_thread_pool

            stats = ["n/a", "n/a", "n/a", "n/a"]
            if isinstance(collect_thread_pool, CollectionThreadPool):
                stats = map(
                    lambda n: str(n),
                    collect_thread_pool.get_stats_working()
                )
            log.warning(("Status of collection threads - \t"
                         + "Collecting: %s\t"
                         + "Alive: %s\t"
                         + "Pool: %s\t"
                         + "Capacity: %s"
                         ) % tuple(stats))
            return
        if parameters[0] == "threads" or parameters[0] == "th":
            import threading

            log.warning("Count of active threads: %d"
                        % threading.active_count())
            return
        log.warning("Unsupported stat")

    def run(self):
        """
        The execution function of PackageThread class:
        loop on message queue and select methods to call with
        respect to commands received.
        :return:
        """
        global package_lock
        global package_startup_list

        # Load packages specified for automatic loading
        with package_lock:
            self._package_load_auto()

        # Listen on message queue for commands
        # Other packages are loaded here according to commands received
        while self.flag_alive:
            msg = package_message_queue.get()
            log.info("Got message in package messenger queue: %s"
                     % ",".join(msg))
            if not isinstance(msg, tuple) and not isinstance(msg, list):
                raise TypeError(type(msg))

            # Switch on message content (command), determine what to do
            command = msg[0]
            if command in ["load", "reload", "update"]:
                #-----------------------------------------------------------
                # Use these commands to handle package management tasks

                with package_lock:
                    offset = 0
                    autoload_flag = False
                    if len(msg) > 1 and msg[1] == '-r':
                        offset = 1
                        autoload_flag = True
                    if len(msg) < (2 + offset):
                        log.warning("No package is specified: %s" % command)
                        continue
                    if len(msg) > (3 + offset):
                        list_arg = msg[(1 + offset):]
                        list_packages = []
                        cnt = len(list_arg)
                        if (cnt % 2):
                            log.warning("Package name and checksum are not paired correctly: %s" % command)
                            continue
                        i = 0
                        while ((i < cnt) and (i+1 < cnt)):
                            list_packages.append({list_arg[i]: list_arg[i+1]})
                            i += 2
                        if command == "load":
                            self._package_load_list(list_packages, autoload_flag)
                        elif command == "update":
                            self._package_update_list(list_packages, autoload_flag)
                        else:
                            log.warning("Batch operation not supported: %s"
                                        % command)
                        continue
                    file_name = msg[1 + offset]
                    if len(msg) == (2 + offset):
                        log.warning("No checksum of {0} is specified: {1}".
                                    format(file_name, command))
                        continue
                    checksum = msg[2 + offset]
                    if command == "load":
                        self._package_load(file_name, checksum, autoload_flag)
                    elif command == "reload":
                        self._package_reload(file_name, checksum, autoload_flag)
                    elif command == "update":
                        self._package_update(file_name, checksum, autoload_flag)
                    else:  # should not happen
                        raise RuntimeError("Command category error")
            elif command in ["unload", "delete"]:
                #-----------------------------------------------------------
                # Use these commands to handle package unload/delete management tasks

                with package_lock:
                    if len(msg) < 2:
                        log.warning("No package is specified: %s" % command)
                        continue
                    if len(msg) > 2:
                        list_packages = msg[1:]
                        if command == "unload":
                            self._package_unload_list(list_packages)
                        elif command == "delete":
                            self._package_delete_list(list_packages)
                        else:
                            log.warning("Batch operation not supported: %s"
                                        % command)
                        continue
                    file_name = msg[1]
                    if command == "unload":
                        self._package_unload(file_name)
                    elif command == "delete":
                        self._package_delete(file_name)
                    else:  # should not happen
                        raise RuntimeError("Command category error")
            elif command == "list":
                with package_lock:
                    if len(msg) != 2:
                        log.warning("Invalid format of command: %s" % command)
                        continue
                    self._cmd_handler_list(msg[1])
            elif command == "stat":
                with package_lock:
                    if len(msg) < 2:
                        log.warning("Invalid format of command: %s" % command)
                        continue
                    self._cmd_handler_stat(msg[1:])
            elif command == "load_auto":
                with package_lock:
                    self._package_load_auto()
            elif command == "unload_all":
                with package_lock:
                    self._package_unload_list(self._packages_loaded.keys())
            elif command == "update_all":
                with package_lock:
                    self._package_update_list(self._packages_loaded.keys())
            elif command == "terminate":
                if self._terminate_all():
                    self.flag_alive = False
                    break
            else:
                log.warning("Unsupported command is dropped")
        log.info("Thread exits: %s" % str(self.name))

    #-----------------------------------------------------------------------
    # This method is called to check if specified package exists

    def _package_chk_exists(self, file_name, ext_forced=None):
        global package_path

        c_slash = "/"
        if package_path.endswith(c_slash):
            c_slash = ""
        path_file = os.path.abspath(package_path + c_slash + file_name)
        if not (path_file.startswith(os.path.abspath(package_path)+'/')):
            log.error("Package %s is NOT under package path %s"
                         % (file_name, package_path))
            return None, None, None

        file_ext = None
        extensions = ["py", "pyc", "pyo"]

        # get checksum for all candidates: path_file + ".py/.pyc/.pyo"
        checksum_list = []
        for ext in extensions:
            checksum = sha1sum(path_file + "." + ext)
            if (checksum is not None):
                checksum_list.append(checksum)

        prompt_ext_all = "py[co]?"
        if not ext_forced:
            for file_ext_ind in extensions:
                if os.path.isfile(path_file + "." + file_ext_ind):
                    file_ext = file_ext_ind
                    break
        else:
            if os.path.isfile(path_file + "." + ext_forced):
                file_ext = ext_forced
        if not file_ext:
            if not ext_forced:
                log.error("Package file not found: %s"
                          % (path_file + "." + prompt_ext_all))
            else:
                log.error("Package file not found: %s"
                          % (path_file + "." + ext_forced))
            return None, None, None
        path_file_ext = path_file + "." + file_ext
        log.debug("Package file found: %s" % path_file_ext)
        return path_file_ext, file_ext, checksum_list

    #-------------------------------------------------------------------
    # Guarantee package record is written into automatic load file.
    # file_name:checksum
    # checksum may need to be updated
    def _write_package_into_autoload(self, file_name, checksum):
        global package_startup_list_path

        output_list = []
        found_record = False
        log.debug("_write_package_into_autoload {0} {1}".format(file_name, checksum))
        if isinstance(package_startup_list_path, basestring):
            try:
                with open(package_startup_list_path, "r+") as fp:
                    output_list = fp.read().splitlines()
                    fp.seek(0)
                    for values in output_list:
                        k, v = values.split(":")
                        if (k != file_name):
                            fp.write(values + '\n')
                        elif ((k == file_name) and (checksum is not None)):
                            fp.write(values + '\n')
                            found_record = True
                    if found_record == False:
                        try:
                            fp.write(file_name + ":" + checksum + '\n')
                        except:
                            log.exception("_write_package_into_autoload write record error")
                    fp.truncate()
            except IOError:
                log.warning("Could not load start-up list from: %s"
                            % package_startup_list_path)
        else:
            log.info("Invalid file path for package automatic loading")

    #-------------------------------------------------------------------
    # remove package record out of automatic load file.
    def _remove_package_from_autoload(self, file_name):
        global package_startup_list_path

        output_list = []
        log.debug("_remove_package_from_autoload {0}".format(file_name))

        if isinstance(package_startup_list_path, basestring):
            try:
                with open(package_startup_list_path, "r+") as fp:
                    output_list = fp.read().splitlines()
                    fp.seek(0)
                    for values in output_list:
                        k, v = values.split(":")
                        if (k != file_name):
                            fp.write(values + '\n')
                    fp.truncate()
            except IOError:
                log.warning("Could not load start-up list from: %s"
                            % package_startup_list_path)
        else:
            log.info("Invalid file path for package automatic loading")

    #-------------------------------------------------------------------
    # Attempt to load package module from file.
    # Supported file types are source files (.py) with highest priority,
    #                          compiled files (.pyc),
    #                      and optimized compiled files (.pyo).
    # Having .py files to have highest priority guarantees that coming
    # packages in .py format can override compiled files of its previous
    # version.

    def _package_module_load(self, file_name, path_file_ext, file_ext):

        module_loaded = None
        module_name = re.sub(r"\.", "_", file_name)
        try:
            if file_ext in ["py"]:
                module_loaded = imp.load_source(
                    module_name,
                    path_file_ext
                )
            elif file_ext in ["pyc", "pyo"]:
                module_loaded = imp.load_compiled(
                    module_name,
                    path_file_ext
                )
            else:  # should not happen
                raise RuntimeError("File extension category error")
        except Exception as err:
            log.exception("Error loading module: %s" % str(err))
            return None, None

        log.debug("Loaded module: %s" % module_loaded.__name__)
        return module_loaded, module_name

    #-----------------------------------------------------------------------
    # This method is called to load package into current Liota process using
    # file_name (no_ext) as package identifier.

    def _package_load(self, file_name, checksum=None, autoload_flag=False,
                      ext_forced=None, check_stack=None):

        log.debug("Attempting to load package:{0}{1}".format(file_name, checksum))

        # Check if specified package is already loaded
        if file_name in self._packages_loaded:
            log.warning("Package already loaded: %s" % file_name)
            return None

        path_file_ext, file_ext, checksum_list = self._package_chk_exists(
            file_name, ext_forced)
        if path_file_ext is None:
            return None

        try:
            # verify file integrity first
            if (checksum is not None):
                verify_flag = False
                for sha1 in checksum_list:
                    if (sha1.hexdigest() == checksum):
                        verify_flag = True
                        break
                if (verify_flag == False):
                    log.error("Package %s integrity verification failed" % path_file_ext)
                    return None
            else:
                sha1 = sha1sum(path_file_ext);
        except IOError:
            log.error("Could not open file: %s" % path_file_ext)
            return None
        log.info("Loaded package file: %s (%s)"
                 % (path_file_ext, sha1.hexdigest()))

        #-------------------------------------------------------------------
        # Following sections do these:
        #   1)     from file path  load module,
        #   2)     from module     load class,
        #   3)     with class      create instance (object),
        #   4) and call method run of created instance.

        module_loaded, module_name = self._package_module_load(
            file_name, path_file_ext, file_ext)
        if module_loaded is None:
            return None

        #-------------------------------------------------------------------
        # Acquire dependency list and recursively load them.
        # If any dependency fails to load, current package will not load.

        dependencies = []
        if hasattr(module_loaded, "dependencies"):
            dependencies = getattr(module_loaded, "dependencies")
            if not isinstance(dependencies, list):
                log.error("Mal-formatted list of dependencies in module %s"
                          % module_loaded.__name__)
                return None

            if len(dependencies) > 0:
                log.info("Package %s depends on: %s"
                         % (file_name, " ".join(dependencies)))
                if not isinstance(check_stack, list):
                    check_stack = []
                check_stack.append(file_name)
                for dependency in dependencies:
                    if dependency in check_stack:
                        log.error("%s is not loaded, because %s depends on it"
                                  % (file_name, dependency))
                        check_stack.pop()
                        return None
                    if dependency not in self._packages_loaded:
                        self._package_load(dependency, check_stack=check_stack)
                    if dependency not in self._packages_loaded:
                        log.error("%s is not loaded, because %s failed to load"
                                  % (file_name, dependency))
                        check_stack.pop()
                        return None

                    # Add dependent record
                    dep_record = self._packages_loaded[dependency]
                    assert(isinstance(dep_record, PackageRecord))
                    dep_record.add_dependent(file_name)
                check_stack.pop()
                log.debug("Dependency check of package %s is complete"
                          % file_name)

        # Get package class from module and instantiate it
        if not hasattr(module_loaded, "PackageClass"):
            log.error("Invalid package: %s" % module_name)
            return None

        klass = getattr(module_loaded, "PackageClass")
        package_record = PackageRecord(file_name)
        try:  # Create instance
            if not package_record.set_instance(klass()):
                log.error("Unexpected failure initializing package")
                return None
        except:
            log.exception("Exception in PackageClass instance creation")
            return None
        try:  # Run created instance
            package_record.get_instance().run(
                self._resource_registry.get_package_registry(file_name)
            )
        except Exception as er:
            log.exception("Exception in initialization: %s" % str(er))
            return None
        package_record.set_sha1(sha1)
        package_record.set_ext(file_ext)
        package_record.set_dependencies(dependencies)
        self._packages_loaded[file_name] = package_record

        # if needed, put package name in automatically load file
        if (autoload_flag == True):
            self._write_package_into_autoload(file_name, sha1.hexdigest())

        log.info("Package class from module %s is initialized"
                 % module_loaded.__name__)
        return package_record

    #-----------------------------------------------------------------------
    # This method is called to unload package using its file_name (no ext).
    # Use track_list to keep track of full file name (with ext) when unloading,
    # so reload can always load exactly that same file
    def _package_unload(self, file_name, track_list=None):
        log.debug("Attempting to unload package: %s" % file_name)

        # Check if specified package is already loaded
        if file_name not in self._packages_loaded:
            log.warning("Could not unload package - not loaded: %s"
                        % file_name)
            return False

        package_record = self._packages_loaded[file_name]
        assert(isinstance(package_record, PackageRecord))

        # Stop all dependents, before making any change to current package
        dependents = package_record.get_dependents()

        if len(dependents) > 0:
            log.info("Package %s is depended by: %s"
                     % (file_name, " ".join(dependents)))
            for dependent in dependents:
                if dependent in self._packages_loaded:
                    self._package_unload(dependent, track_list=track_list)
                if dependent in self._packages_loaded:
                    log.error("%s is still alive, because %s failed to unload"
                              % (file_name, dependent))
                    return False
            log.debug("Dependency check of package %s is complete"
                      % file_name)

        package_obj = package_record.get_instance()
        if not isinstance(package_obj, LiotaPackage):
            raise TypeError(type(package_obj))

        # Deregister resources
        # Unload should proceed no matter deregistration succeeds or not
        if file_name in self._resource_registry._packages:
            for identifier in self._resource_registry._packages[file_name]:
                self._resource_registry.deregister(identifier)
            del self._resource_registry._packages[file_name]
            log.debug("Deregistered resource refs for package: %s"
                      % file_name)
        else:
            log.warning("Could not deregister resource refs for package: %s"
                        % file_name)

        # Clean-up
        try:
            package_obj.clean_up()
        except Exception as er:
            log.exception("Exception in clean-up: %s" % er)

        # Remove dependent item from dependencies
        log.debug("Package %s depends on: %s"
                  % (file_name, " ".join(package_record.get_dependencies())))
        for dependency in package_record.get_dependencies():
            self._packages_loaded[dependency].del_dependent(file_name)
            log.debug("Package %s is no longer a dependent of %s"
                      % (file_name, dependency))

        if isinstance(track_list, list):
            track_list.append((file_name, package_record.get_ext(), package_record.get_sha1().hexdigest()))
        del self._packages_loaded[file_name]

        # if exists, remove package name out of automatically load file
        self._remove_package_from_autoload(file_name)

        log.info("Unloaded package: %s" % file_name)
        return True

    #-----------------------------------------------------------------------
    # This method is called to delete a list of packages.
    # It returns True if all packages in list are successfully deleted.

    def _package_delete_list(self, package_list):
        list_failed = []
        for file_name in package_list:
            log.debug("Attempting to delete packages:{0}".format(file_name))
            try:
                if not self._package_delete(file_name):
                    list_failed.append(file_name)
            except:
                log.exception("_package_delete_list exception")
        if len(list_failed) > 0:
            log.warning("Some packages specified in list failed to delete: %s"
                        % " ".join(list_failed))
        else:
            log.info("Batch delete successful")
        return len(list_failed) < 1

    #-----------------------------------------------------------------------
    # This method is called to reload package.
    # We keep track of full file name (with ext) when unloading, so reload
    # will always load exactly that same file, even if a different higher-
    # priority source file is added before reload.

    def _package_reload(self, file_name, checksum, autoload_flag=False):
        log.debug("Attempting to reload package: {0}{1}".format(file_name, checksum))

        # Check if specified package is already loaded
        if file_name not in self._packages_loaded:
            log.warning("Could not reload package - not loaded: %s"
                        % file_name)
            return None

        # Logic of reload
        track_list = []
        if self._package_unload(file_name, track_list=track_list):
            package_record = None
            track_list.reverse()
            log.info("Packages will be reloaded: %s"
                     % " ".join(
                         map(lambda item: item[0], track_list)
                     )
                     )
            for track_item in track_list:
                log.debug("trace_item:{0}{1}".format(track_item[0], track_item[2]))
                if track_item[0] in self._packages_loaded:
                    continue
                if (track_item[0] == file_name) and (checksum is not None) and (checksum != track_item[2]):
                    temp_record = \
                        self._package_load(track_item[0], checksum, ext_forced=track_item[1])
                else:
                    temp_record = \
                        self._package_load(track_item[0], track_item[2], ext_forced=track_item[1])
                if temp_record is not None:
                    if track_item[0] == file_name:
                        package_record = temp_record
                    log.info("Reloaded package: %s" % file_name)
                else:
                    log.error("Unloaded but could not reload package: %s"
                              % file_name)
            if not package_record is None:
                # if needed, guarantee package name in automatically load file
                if (autoload_flag == True):
                    self._write_package_into_autoload(file_name, package_record.get_sha1().hexdigest())
                return package_record
            else:
                return None
        else:
            log.warning("Could not unload package: %s" % file_name)
        return None

    #-----------------------------------------------------------------------
    # This method is called to update package.
    # We keep track of full file name (without ext) when unloading.
    # The difference between this method and _package_reload is:
    #   1)  If target package is not loaded, this method tries to load it.
    #   2)  For all packages involved in update, this method calls
    #       _package_load to look for source files and compiled files in our
    #       preferred priority order, so updated source file can be used to
    #       update target package even if it was loaded using compiled file.

    def _package_update(self, file_name, checksum, autoload_flag):
        log.debug("Attempting to update package: %s" % file_name)

        # Check if specified package is already loaded
        if file_name not in self._packages_loaded:
            log.info("Package is not loaded, will try to load: %s"
                     % file_name)
            return self._package_load(file_name, checksum)

        # Logic of reload
        track_list = []
        if self._package_unload(file_name, track_list=track_list):
            package_record = None
            track_list.reverse()
            log.info("Packages will be reloaded and updated: %s"
                     % " ".join(
                         map(lambda item: item[0], track_list)
                     )
                     )
            for track_item in track_list:
                if track_item[0] in self._packages_loaded:
                    continue
                if (track_item[0] == file_name) and (checksum is not None) and (checksum != track_item[2]):
                    temp_record = \
                        self._package_load(track_item[0], checksum)
                else:
                    temp_record = \
                        self._package_load(track_item[0], track_item[2])
                if temp_record is not None:
                    if track_item[0] == file_name:
                        package_record = temp_record
                    log.info("Reloaded and updated package: %s" % file_name)
                else:
                    log.error("Unloaded but could not reload package: %s"
                              % file_name)
            if not package_record is None:
                # if needed, guarantee package name in automatically load file
                if (autoload_flag == True):
                    self._write_package_into_autoload(file_name, package_record.get_sha1().hexdigest())
                log.info("Reloaded and updated package: %s" % file_name)
                return package_record
            else:
                return None
        else:
            log.warning("Could not unload package: %s" % file_name)
            return None

    #-----------------------------------------------------------------------
    # This method is called to load a list of packages.
    # If any package in list is already loaded, it will be simply ignored -
    # Neither will this method throw an exception, nor will this package be
    # reloaded.
    # It returns True if all packages in list are successfully loaded.

    def _package_load_list(self, package_list, autoload_flag=False):
        list_failed = []
        for file_string in package_list:
            log.debug("Attempting to load packages:{0}".format(file_string))
            try:
                for file_name, checksum in file_string.items():
                    if file_name in self._packages_loaded:
                        continue
                    if not self._package_load(file_name, checksum, autoload_flag):
                        list_failed.append(file_name)
            except:
                log.exception("_package_load_list exception")

        if len(list_failed) > 0:
            log.warning("Some packages specified in list failed to load: %s"
                        % " ".join(list_failed))
        else:
            log.info("Batch load successful")
        return len(list_failed) < 1

    #-----------------------------------------------------------------------
    # This method is called to unload a list of packages.
    # If any package in list is not loaded, it will be simply ignored -
    # This method will simply assume it is successfully unloaded and won't
    # throw an exception.
    # It returns True if all packages in list are successfully unloaded.

    def _package_unload_list(self, package_list, track_list=None):
        log.debug("Attempting to unload packages: %s"
                  % " ".join(package_list))
        list_failed = []
        for file_name in package_list:
            if file_name not in self._packages_loaded:
                continue
            if not self._package_unload(file_name, track_list=track_list):
                list_failed.append(file_name)

        if len(list_failed) > 0:
            log.warning("Some packages specified in list failed to unload: %s"
                        % " ".join(list_failed))
        else:
            log.info("Batch unload successful")
        return len(list_failed) < 1

    #-----------------------------------------------------------------------
    # This method is called to update a list of packages.
    # It first unload packages in that list, and then load them back.

    def _package_update_list(self, package_list, autoload_flag):
        filename_list = []
        for file_string in package_list:
            log.debug("Attempting to update packages:{0}".format(file_string))
            try:
                for filename, checksum in file_string.items():
                    filename_list.append(filename)
            except:
                log.exception("_package_update_list exception")
        flag_failed = False

        # Acquire a list of all dependents of these packages
        track_list = []
        if not self._package_unload_list(filename_list, track_list=track_list):
            flag_failed = True
        track_list.reverse()

        # Load packages, in case some packages not loaded are to be updated
        if not self._package_load_list(package_list, autoload_flag):
            flag_failed = True

        # Load all dependents
        if len(track_list) > 0:
            track_string_list = []
            map(lambda x: track_string_list.append({x[0]: x[2]}), track_list)
            if not self._package_load_list(track_string_list, autoload_flag):
                flag_failed = True

        if flag_failed:
            log.warning("Some packages failed to update. See log for details")
        else:
            log.info("Batch update successful")
        return not flag_failed

    #-----------------------------------------------------------------------
    # This method is called to load packages that are specified in
    # configuration for automatic loading at start-up.

    def _package_load_auto(self):
        global package_startup_list_path
        global package_startup_list

        output_list = []
        package_startup_list = []

        # Validate start-up list
        if isinstance(package_startup_list_path, basestring):
            try:
                with open(package_startup_list_path, "r") as fp:
                    output_list = fp.read().splitlines()
                for values in output_list:
                    k, v = values.split(":")
                    package_startup_list.append({k: v})
            except IOError:
                log.warning("Could not load start-up list from: %s"
                            % package_startup_list_path)
        else:
            log.info("No package is automatically loaded at start-up")

        # Load packages in a batch
        if len(package_startup_list) > 0:
            self._package_load_list(package_startup_list)

    #-----------------------------------------------------------------------
    # This method is called to delete package. All source files and compiled
    # files associated with specified package name will be affected.
    # It tries to move "deleted" files into a subdirectory called "stash".
    # If moving fails, it then tries to really delete these files.

    def _package_delete(self, file_name):
        global package_path

        log.debug("Attempting to delete package: %s" % file_name)

        # Check if specified package is loaded, if yes, unload first
        if file_name in self._packages_loaded:
            if not self._package_unload(file_name):

                #-----------------------------------------------------------
                # In this case, specified package is already loaded, but
                # we failed to unload it. However, it should be totally fine
                # to delete corresponding file(s) of that package even if
                # it is loaded - at least in Python 2.
                # Therefore, we log this as a warning and continue deletion.

                log.warning("Package is loaded but failed to unload")

        # Find all files associated with this package name
        c_slash = "/"
        if package_path.endswith(c_slash):
            c_slash = ""
        path_file = os.path.abspath(package_path + c_slash + file_name)

        extensions = ["py", "pyc", "pyo"]
        file_names_found = []
        for file_ext_ind in extensions:
            if os.path.exists(path_file + "." + file_ext_ind):
                file_names_found.append(file_name + "." + file_ext_ind)

        if len(file_names_found) < 1:
            log.warning("No source or compiled file found for package: %s"
                        % file_name)
            return False

        # Create stash folder for delete packages
        stash_dir = package_path + c_slash + "stash"
        if not os.path.isdir(stash_dir):
            try:
                os.makedirs(stash_dir)
            except OSError:
                log.warning("Could not create stash directory: %s" % stash_dir)

        # Move files to stash directory
        flag_failed = False
        for file_name_found in file_names_found:
            file_name_src = package_path + c_slash + file_name_found
            try:
                os.rename(
                    file_name_src,
                    package_path + c_slash + "stash/" + file_name_found
                )
                log.debug("File moved to stash: %s" % file_name_found)
            except OSError:
                log.warning("Could not move file: %s" % file_name_src)
                try:
                    os.remove(file_name_src)
                    log.debug("File removed: %s" % file_name_found)
                except OSError:
                    log.error("Could not remove file: %s" % file_name_src)
                    flag_failed = True

        if flag_failed:
            log.warning("Some files failed to delete. See log for details")
        else:
            # if exists, remove package name out of automatically load file
            self._remove_package_from_autoload(file_name)
            log.info("Package is deleted: %s" % file_name)
        return not flag_failed

    #-----------------------------------------------------------------------
    # This method is called to signal termination to all threads in package
    # manager, and calls metric handler to terminate its threads too.
    # Supposedly, it should be able to let Liota exit elegantly.

    def _terminate_all(self):
        global package_messenger_thread
        global package_messenger_pipe

        log.info("Shutting down package messenger...")
        if package_messenger_thread.isAlive():
            with open(package_messenger_pipe, "w") as fp:
                fp.write(
                    "terminate_messenger_but_you_should_not_do_this_yourself\n")

        log.info("Unloading packages...")
        if not self._package_unload_list(self._packages_loaded.keys()):
            log.error("Some packages failed to unload. See log for details")
            return False

        log.info("Terminating metric handler threads...")

        from liota.core.metric_handler import terminate as handler_terminate

        handler_terminate()
        return True


class PackageMessengerThread(Thread):
    """
    PackageMessengerThread does inter-process communication (IPC) to listen
    to commands casted by other processes (potentially from AirWatch, etc.)
    Current implementation of PackageMessengerThread blocks on a named pipe.
    """

    def __init__(self, pipe_file, name=None):
        Thread.__init__(self, name=name)
        self._pipe_file = pipe_file

        # Unblock previous writers
        BUFFER_SIZE = 65536
        ph = None
        try:
            ph = os.open(self._pipe_file, os.O_RDONLY | os.O_NONBLOCK)
            flags = fcntl.fcntl(ph, fcntl.F_GETFL)
            flags &= ~os.O_NONBLOCK
            fcntl.fcntl(ph, fcntl.F_SETFL, flags)
            while True:
                buffer = os.read(ph, BUFFER_SIZE)
                if not buffer:
                    break
        except OSError as err:
            import errno
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
        """
        The execution function of PackageMessengerThread class:
        loop to read messages from messenger namedPipe and put into
        message queue.
        :return:
        """
        global package_message_queue

        while self.flag_alive:
            with open(self._pipe_file, "r") as fp:
                for line in fp.readlines():
                    msg = line.split(',')
                    if len(msg) > 0:
                        if len(msg) == 1 and msg[0] == \
                                "terminate_messenger_but_you_should_not_do_this_yourself":
                            self.flag_alive = False
                            break
                        package_message_queue.put(msg)
        log.info("Thread exits: %s" % str(self.name))

def initialize():
    """
    Create queues and spawns PackageThread, which will loop on commands grabbed
    from a queue and load/unload packages as requested in those commands.
    Initialization should occur when this module is imported for first time.
    :return:
    """
    global is_package_manager_initialized
    if is_package_manager_initialized:
        log.debug("Package manager is already initialized")
        return

    # Validate package path
    global package_path
    assert(isinstance(package_path, basestring))
    if os.path.isdir(package_path):
        try:
            os.listdir(package_path)
        except OSError:
            package_path = None
            log.error("Could not access package path")
            return
    else:
        log.debug("Could not find package path: " + package_path)
        try:
            os.makedirs(package_path)
            log.info("Created package path: " + package_path)
        except OSError:
            package_path = None
            log.error("Could not create package path")
            return

    # Validate package messenger pipe
    global package_messenger_pipe
    assert(isinstance(package_messenger_pipe, basestring))
    if os.path.exists(package_messenger_pipe):
        if stat.S_ISFIFO(os.stat(package_messenger_pipe).st_mode):
            pass
        else:
            log.error("Pipe path exists, but it is not a pipe")
            package_messenger_pipe = None
            return
    else:
        package_messenger_pipe_dir = os.path.dirname(package_messenger_pipe)
        if not os.path.isdir(package_messenger_pipe_dir):
            try:
                os.makedirs(package_messenger_pipe_dir)
                log.info("Created directory: " + package_messenger_pipe_dir)
            except OSError:
                package_messenger_pipe = None
                log.error("Could not create directory for messenger pipe")
                return
        try:
            os.mkfifo(package_messenger_pipe, 0600)
            log.info("Created pipe: " + package_messenger_pipe)
        except OSError:
            package_messenger_pipe = None
            log.error("Could not create messenger pipe")
            return
    assert(stat.S_ISFIFO(os.stat(package_messenger_pipe).st_mode))

    # Will not initialize package manager if package path is mis-configured
    if package_path is None:
        log.error("Package manager failed because package path is invalid")
        return

    # Initialization of package manager
    global package_message_queue
    if package_message_queue is None:
        package_message_queue = Queue()
    global package_lock
    if package_lock is None:
        package_lock = Lock()
    global package_thread
    if package_thread is None:
        package_thread = PackageThread(name="PackageThread")

    # PackageMessengerThread should start last because it triggers actions
    global package_messenger_thread
    if package_messenger_thread is None:
        if package_thread.isAlive():
            package_messenger_thread = \
                PackageMessengerThread(
                    pipe_file=package_messenger_pipe,
                    name="PackageMessengerThread"
                )
        else:
            log.warning("Package messenger will not start")

    # Mark package manager as initialized
    is_package_manager_initialized = True
    log.info("Package manager is initialized")

# Initialization of this module
if not is_package_manager_initialized:
    initialize()

log.debug("Package manager is imported")
