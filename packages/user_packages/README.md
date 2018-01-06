# Liota User Packages

Basic user packages which we believe should exist on the edge system to publish the basic health stats to Pulse IoT Control Center.
These packages should be placed at path "/usr/lib/liota/packages".

* general_edge_system.py

The sample package contains specifications of GeneralEdgeSystem, replace the "EdgeSystemName" with the logic to auto-generate the unique name everytime this package
is loaded based on the user flow. Unique identifier can be from the system(MAC address) or devices to generate the unique name.

* iotcc_mqtt.py

This is a sample user package which creates a IoTControlCenter DCC object and registers edge system on
IoTCC over MQTT Protocol to acquire "registered edge system", i.e. iotcc_edge_system. This package has dependency on credentials package
which is pre-loaded during the installation in order to provide the required credentials and configuration parameters in the liota package manager registry.
The properties for the edge system can be set as 'key:value' pair, you can also set the location by passing the
'latitude:value' and 'longitude:value' as properties in the user package.
If the unregister call is included in the clean up method then the resource will be unregistered and the entire history will be deleted
from Pulse IoT Control Center so comment the logic if the unregsitration of the resource is not required to be done on the package unload.
The retry mechanism has been implemented for important calls like registration, create_relationship or set_property in case of exception. User Configurable Retry and Delay Settings can be tweaked by user as per the targeted scale.

* iotcc_mqtt_edge_system_stats.py

This is a sample user package to publish the basic edge system stats which we believe are required to
monitor the health status of the edge system from Pulse IoT Control Center.
Optional mechanism: If the device raises an intermittent exception during metric collection process it will be required to be handled in the user code
otherwise if an exception is thrown from user code the collection process will be stopped for that metric.
If the None value is returned by User Defined Method(UDM) then metric value for that particular collector instance won't be published.

* iotcc_mqtt_device.py

This is a sample device package which registers five devices to Pulse IoT Control Center and then a relationship is established to Edge System.
A basic UDM returns random value it should be tweaked by user in order to collect device specific metric, all the five devices are loaded with dev_metric.
The retry mechanism has been implemented for important calls like registration, create_relationship or set_property in case of exception.
User Configurable Retry and Delay Settings can be tweaked by user as per the targeted scale.
