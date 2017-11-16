# Using CIP EtherNet Industrial Protocol as Transport in LIOTA

LIOTA offers CIP EtherNet Industrial protocol as transport at Device end via [EtherNetIP_DeviceComms](https://github.com/lucifercr07/liota/blob/can_bus/liota/device_comms/canbus_device_comms.py)

## Starting the server

To get started with the CIP protocol, a server must be started in any linux machine. Install cpppo in that machine using 
"sudo pip install cpppo", then to start the server, "python -m cpppo.server.enip -v Scada=DINT[1]"


## Using EtherNetIP_DeviceComms

Initially run the writer program which keeps writing data to the server, check this [simulator]( ) for the code.
Change the host to the IP of the machine where server is running in line number 6 in this [simulator]( ).

Then, EtherNet/IP related parameters required in `send()` and `receive()` like tags, datatype etc., will be mentioned while starting the server. Please refer this [example](https://github.com/lucifercr07/liota/blob/can_bus/examples/canbus/simulated_canbus.py) which reads the data from the server and send it to DCC.

In SampleProp.conf, the EtherNetIP should be changed to the IP of the server.




