# Device Discovery & Device Simulator
Device Discovery consists of three parts: 

(1) A DiscoveryThread that spawn out various Listener Threads, maintain global data structures and run discovery initialization/clean-up codes,

(2) Discovery Listener Threads which listen on one or more specific communication channels, which could be MQTT subscriber, Coap Server, Socket Server, or a Named Pipe Reader for now, to receive Messages from devices for discovering and registering devices,

(3) Discovery Messenger Threads which listen on a named pipe for now, to provide with an interface for users and automated agents to send commands to Discovery Thread.

Device Discovery will get configuration from liota.conf and initialize the data structures when its own module (`device_discovery.py`) is imported. Once imported, CmdMessengerThread will start listening on a named pipe and DiscoveryThread will spawn out Listener threads.

Device Simulator is a separate debugging and simulation tool for device discovery, which consists of three parts:

(1) A SimulatorThread that spawns out various Simulator Threads, maintain global data structures and run simulator initialization/clean-up codes,

(2) Device Simulator Threads which make use of one or more specific communication channels, which could be MQTT Publisher, Coap Client, Socket Client, or a Named Pipe Writer for now, to send Messages to Liota Device Discovery Listeners for advertising device information, 

(3) Command Messenger Threads which listen on a named pipe for now, to provide with an interface for users and automated agents to send commands to Simulator Thread.

Device Simulator will get configuration from liota.conf and initialize the data structures when its own module (`discovery_simulator.py`) is imported. Once imported, CmdMessengerThread will start listening on a named pipe and DeviceSimulatorThread will spawn out Simulator threads.

### How to Start Device Discovery

Device Discovery could be started through the Liota package of 'dev_disc.py' under the folder of packages/dev_disc/, which will initialize a Device Discovery Thread. If you want it ran automatically when you start package manager, you can put dev_disc/dev_disc inside packages_auto.txt.
To be reminded, to let discovered devices registered to user specified DCCs, at least one DCC package should be loaded.

In details, after installation with (sudo python setup.py install or pip install liota), you can do the following:
# Configuration A (under /etc/liota/conf, inside liota.conf, default/example settings are available)
[IOTCC_PATH]

dev_file_path = /etc/liota/conf/devs   # the folder where store discovered device information files

entity_file_path = /etc/liota/conf/entity # the folder where store discovered device information internally

[DISC_CFG]

disc_cmd_msg_pipe = /var/tmp/liota/disc_cmd_messenger.fifo # the named pipe path for discovery CmdMessengerThread

[DEVICE_TYPE_TO_UNIQUEKEY_MAPPING] # device discovery can only process device types which are listed here, among its attributes,

Press64 = serial		# Unique attribute's key should be specified, e.g., serial or SN

LM35 = SN

Apple56 = SN

Banana23 = serial

[DEVICE_TYPE_TO_DCC_MAPPING]  # for each device type, list each DCC's package name where discovered devices would like to be registered to

LM35 = graphite, iotcc_mqtt, iotcc		# DCC's package might be more than one, since may use different DCCComms, e.g., iotcc_mqtt and iotcc

Press64 = iotcc_mqtt, iotcc		# DCC could be ANY one that liota supports

Apple56 = iotcc_mqtt 	# If a DCC's package is not loaded, no registration will be carried out, while other tasks keep on going

Banana23 = iotcc	# Later user could create Liota Package for discovered devices to start collecting metrics

[DEVSIM_CFG]

devsim_cmd_msg_pipe = /var/tmp/liota/devsim_cmd_messenger.fifo	# the named pipe path for Device Simulator CmdMessengerThread

[DISC_ENDPOINT_LIST]		# Endpoing list where you want discovery listens on and simulator send messages to

							# if no item in this list, Device Discovery will not be started

disc_msg_pipe = /var/tmp/liota/discovery_messenger.fifo		# currently, only support these 4 types

socket = 127.0.0.1:5000						# you can only use some of them by deleting others

mqtt = 127.0.0.1:1883:device_discovery				# IP address should be updated according to your system

coap = 10.1.170.173:5683					# Mqtt broker should be started first before publish/subscribe

								# reference: https://mosquitto.org/download/

[DISC_MQTT_CFG]							# Mqtt with TLS authentication need more settings

broker_username = None						# default setting does not need certificate or password

broker_password = None						# to use it, please change settings

broker_root_ca_cert = /etc/liota/packages/dev_disc/certs/ca.crt

edge_system_cert_file = /etc/liota/packages/dev_disc/certs/client.crt

edge_system_key_file = /etc/liota/packages/dev_disc/certs/client.key

cert_required = CERT_NONE

tls_version = None

userdata = None

protocol = MQTTv311

transport = tcp

cipher = None

in_flight = 20

queue_size = 0

retry = 5

keep_alive = 60

ConnectDisconnectTimeout = 10

# Configuration B (under /etc/liota/packages, inside sampleProf.conf)

Since when device is discovered, it will be registered to DCC based on your [DEVICE_TYPE_TO_DCC_MAPPING] in liota.conf,
it will use DCC credentials. Therefore, please guarantee IOTCC or Graphite section in sampleProf.conf are configured well.

#### [IOTCC] ####
WebSocketUrl = "xxx"

IotCCUID = "admin"

IotCCPassword = "xxx"

#### [GRAPHITE] ####
GraphiteIP = "92.246.246.188"

GraphitePort = 2003

To be reminded, if DCC Liota package is not loaded, i.e., no corresponding DCC instance, although discovery thread can still listens on end points, device registration will not be carried out.

# Start Device Discovery Liota Package (dev_disc.py under /etc/liota/packages/)

a). when keep dev_disc inside packages_auto.txt:

	sudo python liotad.py (add & is optional)

b). when dev_disc is not inside packages_auto.txt:

	start package manager with cmd line in 1., then load device discovery package by

	sudo ./liotapkg.sh load dev_disc/dev_disc

(can check logs through "tail -f /var/log/liota/liota.log")

# Verify Device Discovery is started
messages should be printed out to stdout, e.g.,

	MqttListener is initialized   # when you have Mqtt inside End Point list

	CoapListener is initialized   # when you have Coap inside End Point list

	CoapListerner is running

	NamedPipeListener is initialized # when you have Named Pipe inside End Point list

	NamedPipeListener is running

	MqttListener is running

	SocketListener is initialized  # when you have Socket inside End Point list

	SocketListener Server started!

(if running or started are printed out, listeners are started successfully)

You can also use CmdMessage to check certain information (under /etc/liota/packages/dev_disc)

	sudo ./liota_disc_pipe.sh list th

	sudo ./liota_disc_pipe.sh list dev

	sudo ./liota_disc_pipe.sh list cfg

### How to Start Device Simulator
Device Simulator Must BE started after Device Discovery module is imported; and should be started
separately by (under /etc/liota/packages/dev_disc)

	sudo python liota_devsim_load.py (add & is optional)

Verification messages are as followings.

	MqttSimulator is initialized

	MqttSimulator is initialized

	CoapSimulator is initialized

	CoapSimulator is running

	NamedPipeSimulator is initialized

	NamedPipeSimulator is running

	SocketSimulator is initialized

	SocketSimulator is running...

You can also use CmdMessage to check certain information (under /etc/liota/packages/dev_disc)

	sudo ./liota_devsim_pipe.sh list th

# In addition, currently the messages sent from device simulators are hard coded (under source code
liota/dev_sims/coap.py (or mqtt.py, named_pipe.py, socket_clnt.py), and inside run()), like

        msg = {

            "Apple56": {

                "k1": "v1",

                "SN": "0",

                "kn": "vn"

            }

        }

where Apple56 is the device type, and its value is attributes. We also have message counter control through, e.g.,

            if i >=10: xxx

            else:

                msg["Apple56"]["SN"] = str(i)

Please modify them corresponding to your settings in liota.conf!!!

## Commands for Both Device Discovery & Device Simulator

Currently, supported commands include action commands and statistical commands.

### action commands

* **terminate**

Stop DiscoveryThread or SimulatorThread, and terminate and cleanup spawned out threads from them.

###Statistical commands

* **stat** th

Print statistical data in Liota log about Python threads.

* **list** dev|res|th|cfg|res

Print a list of discovered devices, resources (configuration or stored objects) and threads respectively
(only cfg and th are available for SimulatorThread).
