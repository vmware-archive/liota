
# LIOTA
Little IoT Agent (liota) is an open source offering for IoT solution developers and resides primarily on IoT gateways.
Liota has been generalized to allow, via modules,
interaction with any data-center component, over any transport, and for any IoT gateway. It is easy-to-use and provides
enterprise-quality modules for interacting with IoT Solutions.

## Design
The primary liota design goals are simplicity, ease of use, easy install, and easy modification. Secondary design goals are
generality, modularity, and enterprise-level quality.

# The Basic Layers of Liota

## Board Layer
The board layer is the base layer of liota and provides an abstraction for IoT gateway hardware. Items one might put in here
are unique i/o architecture, communication physical interfaces, and any other features particular to the system board.

## Gateway Layer
The gateway layer is a sub-module of board and abstracts both the system board and the operating system.
The gateway is defined using the following parameters make, model, and the current OS version installed on them. The functions
provided by this layer are used to configure i/o endpoints, read data from endpoints connected to sensors, or pass commands
to the endpoints of connected actuators as well as any unique OS features.

## Things Layer
This layer (after the 'Things' in Internet-of-Things') allows developers to create representative objects in liota for devices that will
be connected to the gateway, e.g., as USB temperature sensor connected to the gateway.

## Transformer Layer
This layer defines the base structure for creating representations of metrics in liota. A metric is the term for a stream of
numeric values. Metric is a class that
abstracts and represents this stream of values collected from, typically, attached sensors but can be collected from anywhere.
Within the definition of metrics we support SI units are in order to provide units-based
typing for values collected from a sensor. This meta-data can be passed to the data-center component in a format defined by that
component.

## Transport Layer
This layer abstracts the network connectivity between a gateway object and a DCC (Data center component). Currently, liota supports
WebSocket and plain old BSD sockets. In near future it will support MQTT and CoAP. Both are ‘Session’ or layer-5 protocols. MQTT is a
pub-sub system using TCP and CoAP implements reliable UDP datagrams and a data format specification. These protocols are capable of
satisfying most use cases for transferring data from IoT gateways to data-center components. With the current implementation the
gateway acts as either a WebSocket client, establishing a connection with the server using the WebSocket protocol. e.g.
```web
wss://host:port/path
```
or a traditional socket endpoint.

## DCC (Data Center Component)
This layer takes care of supporting DCC’s, which can be hosted anywhere; on-prem, public or private cloud. It is potentially the most
important and complex layers of liota. It provides flexibility to developers for choosing the data-center components they need and
using API’s provided by liota. With help of this layer developers may build custom solutions. The layer implements basic API’s and
encapsulates them into unified common API’s required to send data to various DCC’s. Graphite and vROps (vRealize Operations) are
currently the data-center components supported by the first version of liota. New DCC’s can easily be integrated in this layer as it
follows a plug in-plug out design.

Liota – Sample Code Below is a sample code developed using liota for a representative IoT gateway. A temperature
metric is defined and its values are collected from a USB-temperature sensor connected to the USB-1 port of the gateway. 
The metric values are streamed to vROps;

```python
from liota.boards.gateway_de5000 import DellEdge5000
from liota.things.USB-Temp import USB-Temp
from liota.dcc.vrops import Vrops
from liota.transports.web_socket import WebSocket
# DCC Component
vROps vrops = Vrops(vrops_login, vrops_pwd, WebSocket(URL "secure"))
# GW creation
gw = DellEdge5000("Demo Gateway")
# Device definition
temp = USB-Temp(parent=gw, 'Temp', READ, usb-1)
# Register the Gateway and associated device 
vrops.register(gw)
# Property creation on Gateway 
gw.set_properties("Location", "Palo Alto Prom:E")
# Creating Metric
temperature = vrops.create_metric(temp,'Room Temperature', SI.Celsius, sampling_interval=10)
# Publishing value to DCC component
temperature.start_collecting()
```

## SI Units
Liota supports SI units and the conversion of the units with help of Pint library which is included in liota package to provide
developers the capability to use SI units in their code. We have also included the example [graphite_withTemp.py] (https://github.com/vmware/liota/blob/master/example/graphite_withTemp.py)
which uses the library to convert temperature value from Celsius to Fahrenheit and Kelvin. More details on the usage of the Pint library
and conversion of units can be found at this [link] (https://pint.readthedocs.io/en/0.7.2/index.html).

## Liota – Future Enhancements
Toward the goal of ubiquity for liota we plan to include the following enhancements:
* Enhancements for SI Units support in liota specifically for IoT
* Full support for IEEE 1451, Electronic Transducer Data Sheets
* Support for MQTT and CoAP as transports
* A mechanism for IoT gateways to create planet-wide unique identifiers (possibly based on the blockchain mechanism)
* Support for an actions framework for gateway-defined actions initiate either locally or by data-center components
* Support for popular IoT ingestion engines
* Language bindings apart from Python, starting with C, C++, Java and Lua

# Installation and Testing
In general, liota can be installed with:
```bash
  $ sudo pip install liota
```

It requires a Python 2.7 environment already installed.


## Liota.conf
Right now there is only one item in the liota.conf, where to find a file called logging.json which holds the
dafault initialization parameters for logging. When initialing, liota looks in the current
working directory, '.', the user's home directory '~', a LIOTA_CONF environment variable, and
finally the default location for every install, /etc/liota/conf for liota.conf.

Here is the default, v0.7, liota.conf file

```bash
[LOG_CFG]
json_path = /etc/liota/conf/logging.json
```
Feel free to modify liota.conf and loggin.json as appropriate for your testing.


## Examples
Post-installation the sample codes for publishing the data to DCC can be found at following location;
```bash
  /etc/liota/example
```

Please look through the example code noting especially the files sampleProp.conf and vrops_graphite_dk300_sample.py

Then as an initial test you could bring up an instance of Graphite using the docker instructions found at this [link] (https://github.com/hopsoft/docker-graphite-statsd).

set the appropriate values in sampleProp.conf,
```bash
GraphiteMetric = <a dot separated string> "Mymetric.foo.bar.random"
GraphiteIP = <The IP address of the graphite instance you just brought up>
GraphitePort = <typically 2003> # You can test easily be sending directily to carbon
```

and execute
```bash
  $ sudo nohup python graphite_simulated.py &
```

If you would like to test against an instance of vRealize Operations Manager please send
an email to us at:

```web
liota@vmware.com
```
and we'll work with you to get one set up and help with the necessary values in the properties file.

## Log Location

The default location for log files generated during Liota operation can be found at following
location;

```bash
  /var/log/liota
```
If the above directory is not available or is not writeable modify the log location in the file
logging.json (find it as described above in the section on liota.conf)

## Contributing to Liota

Want to hack on Liota and add your own DCC component? Awesome!
Just fork the project in order to start contributing the code.

## Licensing
Liota is licensed under the BSD 2-Clause License.
