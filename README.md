# LIOTA
Little IoT Agent (liota) is an open source project offering some convenience for IoT solution developers in creating IoT Edge System data orchestration applications. Liota has been generalized to allow, via modules, interaction with any data-center component, over any transport, and for any IoT Edge System. It is easy-to-use and provides enterprise-quality modules for interacting with IoT Solutions.

## Design
The primary liota design goals are simplicity, ease of use, easy installation and easy modification. Secondary design goals are generality, modularity and enterprise-level quality.

# The Basic Abstractions of Liota
The six basic abstractions of liota represent a complete data flow from a device attached to the edge system to an application in a data-center. These are 'Device' (some data source on or attached to the edge system), 'DeviceComms' (communication protocols used between devices and the edge system), 'EdgeSystem' (the edge system hardware and software platforms), 'Metric' (represents a time-series stream from a data source to a data-center application), 'DCCComms' (communication protocols between the edge system and a data-center), and 'DCC' (data-center component, i.e., an ingestion application in a data-center). We have abstract classes for all six of these constructs in a small object hierarchy and a number of concrete classes that comprise this release of liota and allow a liota package or set of packages to create complete data flows from a data source to a component in a data-center.

## Entities
Entities represent abstractions for the three main passive constructs: System, Devices and Metrics that can be, depending on the DCC, registered with the DCC. Such registration typically creates a concrete representation (let's call these 'Resources' simply to differentiate from the local representation we'll call objects) in the data-center component for the local object. Various pieces of meta-data can be associated with the Resource typically created during or after registration. Examples of such meta-data associated with the Resource, metrics, entries in a key/value store, relationships to other Resources, alerts and actions.

Each DCC must implement a register() method and return a RegisteredEntity object. The registered entity object may include any specific data, e.g., uuid, that the DCC may need to refer to the Resource representing the entity object. An entity may be registered with multiple DCCs in the same liota package or set of packages.

### EdgeSystems and Devices
The abstract subclasses of Entities, EdgeSystem and Device are for now mostly placeholders in the hierarchy. We expect, as concrete implementations are created over time we'll see some common data and logic that we can move up into the abstract classes.

**Note:** We recommend creating EdgeSystem Objects before creating DCCComms or DeviceComms objects.

### Metrics
The Metric subclass of Entity is the local object representing a stream of (number, timestamp) tuples. Metrics may be registered with one or more DCCs and the DCC returns a registered metric object. The metric object includes a sampling function which is a user defined method (udm), a sampling frequency stating the interval between subsequent executions of the udm and an aggregation count stating how many executions of the udm to aggregate before sending to the DCCs to which the metric has been registered. An important piece of meta-data liota supports are SI units and a prefix eliminating any confusion as to what the stream of numbers represent.

## DeviceComms
The abstract class DeviceComms represent mechanisms through which devices send and receive data to/from edge systems. Some examples are CAN bus, Modbus, ProfiNet, Zibgee, GPIO pins, Industrial Serial Protocols as well as sockets, websockets, MQTT, CoAP. The DeviceComms abstract class is a placeholder for these various communication mechanisms.

## DCCComms
The abstract class DCCComms represents communication protocols between edge systems and DCCs. Currently, liota supports MQTT, WebSocket and plain old BSD sockets. In near future it will support CoAP. MQTT, WebSocket and CoAP are 'Application' or layer-7 protocols. MQTT is a pub-sub system using TCP and CoAP implements reliable UDP datagrams and a data format specification. These protocols are capable of satisfying most of the use cases for transferring data from IoT gateways to data-center components. With the current implementation the gateway acts as MQTT, WebSocket or a traditional Socket client.

## DCC (Data Center Component)
The abstract class DCC represents an application in a data-center. It is potentially the most important and complex abstraction of liota. It provides flexibility to developers for choosing the data-center components they need and using API's provided by liota. With help of this abstraction developers may build custom solutions. The abstract class states basic methods and encapsulates them into unified common API's required to send data to various DCC's. Graphite and Project Ice are currently the data-center components supported with AWS, BlueMix and ThingWorx to come soon. New DCC's can easily be integrated in the abstraction.

## Transports
Liota supports plain old BSD sockets, WebSocket and MQTT communication protocols.  Refer [MQTT](https://github.com/vmware/liota/blob/master/examples/mqtt/README.md) to know more on different MQTT configuration options available.

## Identity and TLS Configurations
* Identity class encapsulates certificates or credentials related to a connection used at both DCC and Device side.
* TLSConf class encapsulates parameters related to TLS configuration.


## Package Manager
Liota applications can be broken into small pieces that can be loaded and unloaded into a running liota process. We recommend putting the EdgeSystems, Devices, Metrics and DCC(s) in separate packages. Then each construct can be loaded and unloaded at will. See the README in the package directory for complete details.

## Device Discovery
Liota SDK provides users a way to discover new devices at run-time through a dedicated discovery thread. The discovery thread could listen on a list of end points by spinning up a listening thread for each of them. Currently, Liota supports 4 kinds of end points: MQTT, COAP, Socket, and Named Pipe.

Assume there is a list of DeviceType-to-DCC Mappings, such as {TypeA:[DCC1-Package-Name, DCC2-Package-Name], TypeB:[DCC3-Package-Name]}. Listening thread waits for a json message from devices, registers new devices with each DCC in the mapping list, sets any properties, fills out device file for AW agent. AW agent enrolls discovered device and pushes content to bring the device to compliance.

The json message from devices starts with Device Type and comprises a dictionary, that is,
{ 'DeviceType':{key1:value1,key2:value2, ..., keyn:valuen}} e.g., {LM35:{k1:v1,...,SN:12345,kn:vn}}. Assume there is specified unique key for each 'Type' of devices, e.g.,
[{'Type':'LM35', 'UniqueKey':'SN'}]. We will concatenate the type and unique id to LM35_12345 and use this as the name to register the device.

See the README in the dev_disc directory under package directory for complete usage details.

## SI Units
Liota supports SI units and the conversion of the units with help of Pint library which is included in liota package to provide developers the capability to use SI units in their code. We have also included the example [simulated_graphite_temp.py](https://github.com/vmware/liota/blob/master/examples/simulated_graphite_temp.py) which uses the library to convert temperature value from Celsius to Fahrenheit and Kelvin. More details on the usage of the Pint library and conversion of units can be found at this [link](https://pint.readthedocs.io/en/0.7.2/index.html).

## Liota - Future Enhancements
Toward the goal of ubiquity for liota we plan to include the following enhancements:
* Full support for IEEE 1451, Electronic Transducer Data Sheets
* Support for CoAP as transports
* A mechanism for IoT Edge Systems to create planet-wide unique identifiers (possibly based on the blockchain mechanism)
* Support for actions framework for edge-system defined actions initiated either locally or by data-center components
* Support for popular IoT ingestion engines
* Language bindings apart from Python, starting with C, C++, Java and Lua

# Installation and Testing
In general, liota can be installed with:
```bash
  $ sudo pip install liota
```

It requires a Python 2.7 environment already installed.

## Autostarting Liota Daemon
For starting liotad.py in background automatically at reboot perform the following steps:

* Copy autostartliota script present in scripts folder to location:
```bash
  /etc/init.d/
```

To enable/disable the autostart service perform the following steps:

### On Debian/Ubuntu:

* Execute :
```bash
  $ sudo update-rc.d autostartliota defaults
  $ sudo invoke-rc.d autostartliota start
```

* To stop the script and remove it from different runlevels, execute:
```bash
  $ sudo update-rc.d -f autostartliota remove
```

### On RHEL/CentOS:

* To add the script to different runlevels (rc[0-6].d folders), execute:
```bash
  $ chkconfig --add autostartliota
```

* To start it, execute the following command and reboot the system:
```bash
  $ chkconfig autostartliota on
```

* To stop the script, execute:
```bash
  $ chkconfig autostartliota off
```

* To remove the script from different runlevels (rc[0-6].d folders), execute:
```bash
  $ chkconfig --del autostartliota
```

## Liota.conf
liota.conf provides path to find out various configuration & log files. When initializing, liota does a multi-step search for the configuration file:
* Looks in the current working directory '.'
* User's home directory '~'
* A LIOTA_CONF environment variable
* Finally the default location for every installation: /etc/liota/conf.

Here is the default liota.conf file:

```bash
[LOG_CFG]
json_path = /etc/liota/conf/logging.json

[LOG_PATH]
log_path = /var/log/liota

[UUID_PATH]
uuid_path = /etc/liota/conf/uuid.ini

[IOTCC_PATH]
dev_file_path = /etc/liota/conf/devs
entity_file_path = /etc/liota/conf/entity
iotcc_path = /etc/liota/conf/iotcc.json

[PKG_CFG]
pkg_path = /etc/liota/packages
pkg_msg_pipe = /var/tmp/liota/package_messenger.fifo
pkg_list = /etc/liota/packages/packages_auto.txt
```
Feel free to modify [liota.conf](https://github.com/vmware/liota/blob/master/config/liota.conf) and [logging.json](https://github.com/vmware/liota/blob/master/config/logging.json) as appropriate for your testing.


## Examples
Post-installation the sample codes for publishing the data to DCC can be found at following location:
```bash
  /etc/liota/examples
```

Please look through the example code noting especially the files sampleProp.conf and dk300_edge_system_iotcc.py

Then as an initial test you could bring up an instance of Graphite using the docker instructions found at this [link](https://github.com/hopsoft/docker-graphite-statsd).

set the appropriate values in sampleProp.conf,
```bash
GraphiteMetric = <a dot separated string> "Mymetric.foo.bar.random"
GraphiteIP = <The IP address of the graphite instance you just brought up>
GraphitePort = <typically 2003> # You can test easily by sending directly to carbon
```

and execute
```bash
  $ sudo nohup python simulated_graphite_event_based.py &
```

If you would like to test against an instance of Project Ice please send an email to us at:

```web
liota@vmware.com
```
and we'll work with you to get one set up and help with the necessary values in the properties file.

## Log Location

The default location for log files generated during Liota operation can be found at:

```bash
  /var/log/liota
```
If the above directory is not available or is not writeable then modify the log location in the file logging.json (find it as described above in the section on liota.conf)

## Contributing to Liota

Want to hack on Liota and add your own DCC component? Awesome!
Just fork the project in order to start contributing the code.

## Licensing
Liota is licensed under the BSD 2-Clause License.
