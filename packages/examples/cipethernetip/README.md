# Using CIP EtherNet Industrial Protocol as Transport in LIOTA

LIOTA offers CIP EtherNet Industrial protocol as transport at Device end via [cip_ethernet_ip_device_comms](https://github.com/NithyaElango/liota/blob/CipEthernetIP/liota/device_comms/cip_ethernet_ip_device_comms.py)

## Starting the server

To get started with the CIP protocol, a server must be started in any linux machine. Install cpppo in that machine using 
"sudo pip install cpppo", then to start the server, "python -m cpppo.server.enip -v Scada=DINT[1]"


## Using cip_ethernet_ip_device_comms

Initially run the writer program which keeps writing data to the server, check this [simulator](https://github.com/NithyaElango/liota/blob/CipEthernetIP/tests/cipethernetip/cip_ethernet_ip_simulator.py) for the code.
Modify the variable "host" in this [simulator](https://github.com/NithyaElango/liota/blob/CipEthernetIP/tests/cipethernetip/cip_ethernet_ip_simulator.py) if the server is running in a different machine. If not, the server,simulator and liota program are running in  the same machine, then nothing needs to be changed.

Then, EtherNet/IP related parameters required in `send()` and `receive()` like tags, datatype etc., will be mentioned while starting the server. Please refer this [example](https://github.com/NithyaElango/liota/blob/CipEthernetIP/packages/examples/cipethernetip/cip_socket_graphite.py) which reads the data from the server and send it to DCC.

In SampleProp.conf, the CipEtherNetIp should be changed to the IP of the server, if the server is running in a different machine.Alos, the Tag should be changed if anyother tag is mentioned while starting the server other than Scada.




