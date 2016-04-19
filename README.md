
# LIOTA
Liota (Little IoT Agent) is open source offering for the IoT application developers. Liota is been generalized to interact with any
data-center component, over any transport, and on any IoT gateway. It is easy-to-use and provides enterprise-quality modules for
interacting with IoT Solutions.

## Design
The primary liota design goal is simplicity, ease of use, easy install, and easy modification. Secondary design goals are generality,
modularity, and enterprise-level.

The basic layers of liota:

## Gateway layer
It is the base layer of liota that provides abstraction for the supported hardware gateways, their unique i/o
architecture, and any unique OS features. Sub-modules are created for the hardware gateways belonging to the same family like the x86
/Intel Galileo and Arduino development platforms that have, more or less, the same i/o architecture. The gateway is defined using the
following parameters make, model, and the current OS version installed on them. The functions provided by this layer are used to
configure i/o endpoints, read data from endpoints connected to sensors, or pass commands to the endpoints of connected actuators. The
gateway layer has a sub-layer termed as “Things”, which allows users to create representative objects in liota for devices that will
be connected to the gateway, e.g., temperature sensor connected to an Intel DK-300 gateway.

## Transformer Layer
This layer defines the base structure for creating representations of metrics and super-metrics in liota. Metric is a class that
abstracts and represents the stream of values collected from attached sensors. A super-metric is a functional composition of one or
more metrics. A super-metric is usually defined whenever more than one metric is required to define the behavior of the environment as
in case of vROps (vRealize Operations). Within the definition of metrics we support SI units are in order to provide units-based
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
encapsulates them into unified common API’s required to send data to various DCC’s. Graphite5 and vROps (vRealize Operations) are
currently the data-center components supported by the first version of liota. New DCC’s can easily be integrated in this layer as it
follows a plug in-plug out design.

Liota – Sample Code Below is a sample code developed using liota for the Intel DK-3006 IoT gateway. A temp metric is defined and its
values are collected from a USB-temperature sensor connected to the USB-1 port of the DK-300. The metric values
are streamed to vROps;

```python
  import liota.boards.Dk300
  import liota.things.USB-Temp
  import liota.DCCs.Vrops
  import liota.transports.WebSocket
  import liota.transformers.Metric
  # DCC Component
  vROps vrops = Vrops(vrops_login, vrops_pwd, WebSocket(URL "secure"))
  # GW creation
  gw = Dk300("Demo Gateway", uuid=get_mac_addr())
  # Device definition
  temp = USB-Temp(parent=gw, 'Temp', READ, usb-1)
  # Register the Gateway and associated device vrops.register(gw)
  # Property creation on Gateway gw.set_properties("Location", "Palo Alto Prom:E")
  # Creating Metric
  temperature = vrops.create_metric(temp,'Room Temperature', SI.Celsius, sampling_interval=10)
  # Publishing value to DCC component
  temperature.start_collecting()
```


## Liota – Future Enhancements
Toward the goal of ubiquity for liota we plan to include the following enhancements:
* Full support for SI Units specification (possibly with enhancements specifically for IoT)
* Full support for IEEE 1451, Electronic Transducer Data Sheets
* Support for MQTT8 and CoAP9 as transports
* A mechanism for IoT gateways to create planet-wide unique identifiers (possibly based on the blockchain mechanism)
* Support for an actions framework for gateway-defined actions initiate either locally or by data-center components
* Support for popular IoT ingestion engines
* Language bindings apart from Python, starting with C, C++, Java and Lua

## Installation
In general, liota can be installed with:
```bash
  $ pip install liota
```

It requires a Python 2.7 environment already installed.

## Examples
Post-installation the sample codes for publishing the data to DCC can be found at following location;
```bash
  /etc/liota/examples
```
In order to run the sample code, please enter the required details in sampleProp.py and start the agent in the following way;
```bash
  $ nohup python vrops_graphite_dk300_sample.py &
```

## Log Location

The log generated during Liota operation can be found at following location;

```bash
  /etc/var/log
```
## Contributing to Liota

Want to hack on Liota and add your own DCC component? Awesome!
Just fork the project in order to start contributing the code.

## Licensing
Liota is licensed under the BSD 2-Clause License.
