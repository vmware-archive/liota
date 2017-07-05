#Liota Package Manager
Liota package manager consists of two parts: (1) A PackageThread that actually loads files, maintain global data structures and run package initialization/clean-up codes and (2) A PackageMessengerThread which listens on one or more specific communication channels, which is a named pipe for now, to provide with an interface for users and automated agents to send commands to package manager.

Package manager will initialize the data structures and threads when its own module (`package_manager.py`) is imported. Once imported, PackageMessengerThread will start listening on the pipe and PackageThread will load all packages specified in the auto list in a batch.

##PackageThread

Currently, supported commands include package action commands and statistical commands.

###Package action commands

* **load** package_name sha1_checksum [package_name sha1_checksum] ...

Load a package with the specified name and its sha1 checksum. For example, linux os user can first use "sha1sum filename" cmd to get checksum, and then load package by
"./liotapkg.sh load filename sha1_checksum".

A python file of cal_sha1sum.py is also provided to help you calculate checksum for a file:
python cal_sha1sum.py file_name (could be relative or absolute file name). For example, under /etc/liota/packages,
python cal_sha1sum.py iotcc_mqtt.py

If the specified package provides with a list of dependencies, recursively load all its dependencies. If more than one package names are specified, load them (as well as their dependencies) in a batch and no package will be loaded twice or reloaded.

Liota packages must follow certain formats for package manager to process them correctly. It is up to the package developer to follow the format requirements. Details will be provided in later parts of this document. Please also refer to `packages` and `packages/example` for example packages we have provided.

If dependency lists of specified packages and their dependencies contain loops, all packages involved in the loop are not to be loaded.

* **unload** package_name [package_name] ...

Unload a package with the specified name. If the specified package has dependents loaded, recursively unload all its dependents. If more than one package names are specified, unload them (as well as their dependents) in a batch.

To `unregister` an entity while unloading set the following flag in `packages/sampleProp.conf` to `True`:
```bash
ShouldUnregisterOnUnload = "True"
```

* **reload** package_name sha1_checksum

Unload a package with the specified name and attempt to reload the same package **using the same file name**. Batch operation is not supported for reloading. If the specified package is not loaded when this command is invoked, the command will fail.

* **update** package_name sha1_checksum [package_name sha1_checksum] ...

Unload a package with the specified name and attempt to reload the same package. If the specified package has dependents loaded, attempt to recursively update all these dependents. If the specified package is not loaded when this command is invoked, skip unloading and load the specified package directly.

* **delete** package_name

Remove a package with the specified name. By default, the removed package will be stashed into a separate folder in the package path, so package manager will not find it. However, if package manager fails to create the folder, or fails to move the file, the package file will be deleted from the file system.

###Package Load Automation

Load Liota Packages automatically when Package Manager starts by listing package names and checksums in the file specified by pkg_list in [PKG_CFG] of liota.conf, e.g., by default /etc/liota/packages/packages_auto.txt (Should NOT have " " around ":"):
package_name:sha1_checksum
[package_name:sha1_checksum]

There are 2 options to add liota package names and checksum:
1. manually write into pkg_list file;
2. add at run time through command [load, reload, update] by specifiying option of "-r", e.g.,
"./liotapkg.sh load -r filename sha1_checksum".
To be reminded, unload command will remove it from pkg_list file.

###Statistical commands

* **stat** met|col|th

Print statistical data in Liota log about metrics, collectors and Python threads respectively.

* **list** pkg|res|th

Print a list of package, resources (shared objects) and threads respectively.

**Note:** PackageThread is just a single thread. If your package contains time-costly or blocking lines in its `run()` or `clean_up()` methods, it will cause PackageThread to wait/block and stop accepting coming commands.

##PackageMessengerThread

PackageMessengerThread listens on a named pipe whose location is defined in `liota.conf`. It then parses texts received from the pipe into commands and arguments and sends them to PackageThread.

Different techniques can be supported in PackageMessengerThread in the future.

##LiotaPackage

There is a LiotaPackage class defined in `package_manager.py` which looks like
```python
class LiotaPackage:
    """
    LiotaPackage is ABC (abstract base class) of all package classes.
    Here it should define abstract methods that developers should implement.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self, registry):
        raise NotImplementedError

    @abstractmethod
    def clean_up(self):
        raise NotImplementedError
```

Developers are required to implement their packages by inheriting from LiotaPackage and implementing the two abstract methods `run()` and `clean_up()`. `run()` is called upon initialization, which may establish necessary communication channels, parse configuration files and create metrics using user defined methods as sampling functions. Developers need to explicitly register shared objects in `run()`, if they want these objects to be accessible by other packages. `clean_up()` is called upon package unloading, which may involve notifying auxiliary threads to stop, notifying metrics to stop collecting and other cleaning ups.

**Note:** Package manager will not do things that it cannot do, for example, terminating an auxiliary thread that is blocked on I/O. In this way, it is up to the developers to write non-blocking codes and create only stoppable threads (or not at all). If the package file contains syntax errors or significant logic errors, the behavior of package manager is undefined.

See our examples for actually working packages.
