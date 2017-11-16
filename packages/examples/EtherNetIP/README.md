# Using CIP EtherNet Industrial Protocol as Transport in LIOTA

LIOTA offers CIP EtherNet Industrial protocol as transport at Device end via [EtherNetIP_DeviceComms](https://github.com/NithyaElango/liota/blob/EtherNet-IP/liota/device_comms/EtherNetIP_DeviceComms.py)

### Starting the server

To get started with the CIP protocol, a server must be started in any linux machine. Install cpppo in that machine using 
"sudo pip install cpppo", then to start the server, "python -m cpppo.server.enip -v Scada=DINT[1]"


### Using EtherNetIP_DeviceComms

Initially run the writer program which keeps writing data to the server, check this [simulator](https://github.com/NithyaElango/liota/blob/EtherNet-IP/examples/EtherNetIP/EtherNetIP_Simulator.py) for the code.
Change the host to the IP of the machine where server is running in line number 6 in this [simulator](https://github.com/NithyaElango/liota/blob/EtherNet-IP/examples/EtherNetIP/EtherNetIP_Simulator.py).

Then, EtherNet/IP related parameters required in `send()` and `receive()` like tags, datatype etc., will be mentioned while starting the server. Please refer this [example](https://github.com/NithyaElango/liota/blob/EtherNet-IP/packages/examples/EtherNetIP/CipSocketGraphite.py) which reads the data from the server and send it to DCC.

In SampleProp.conf, the EtherNetIP should be changed to the IP of the server [SampleProp](https://github.com/NithyaElango/liota/blob/EtherNet-IP/packages/sampleProp.conf)


