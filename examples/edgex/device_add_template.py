# -*- coding: utf-8 -*-
from liota.core.package_manager import LiotaPackage
from random import randint
import time
import socket
import logging
import random
import json
import httplib
from liota.lib.utilities.utility import systemUUID

####huaqiao####
import paho.mqtt.client as mqtt_edgex

log = logging.getLogger(__name__)

dependencies = ["iotcc_mqtt"]

# --------------------User Configurable Retry and Delay Settings------------------------------#

# The value mentioned below is the total number of Edge System being deployed in the infrastructure
# minimum 1 for 1K, 2 for 2K, 3 for 3K, 4 for 4K and  5 for 5K Edge Systems
no_of_edge_system_in_thousands = 1
# Number of Retries for Connection and Registrations
no_of_retries_for_connection = 5
# Retry delay Min Value in seconds
delay_retries_min = 600
# Retry delay Max Value in seconds
delay_retries_max = 1800

# Lambda Function Multiplier uses the above settings for calculating retry and delay logic
lfm = lambda x: x * no_of_edge_system_in_thousands
retry_attempts = lfm(no_of_retries_for_connection)
delay_retries = random.randint(lfm(delay_retries_min), lfm(delay_retries_max))


#######by huaqiao zhang
edgexmeta = {'test':'test'}
device_name = ""
device_value_name = ""
device_data = 0

def on_connect(client,userdata,flags,rc):
    log.info("--------Connection from Edgex Foundry with result code" + str(rc))
    global edgexmeta
    client_edgex.subscribe(edgexmeta["topic"])

def on_message(client,userdata,msg):
    log.info("----------edgexfoundry msg: "+msg.topic + " " + str(msg.payload))
    global device_name
    global device_value_name
    global device_data
    edgex_data_tmp = json.loads(msg.payload)
    if edgex_data_tmp["device"] == device_name:
    	readings = edgex_data_tmp["readings"]
    	readObj = readings[0]
    	if readObj["name"] == device_value_name:
    		device_data = readObj["value"]
                log.info("-------- Data From EdgeX Foundry: " + str(device_data))

client_edgex = mqtt_edgex.Client()

def mqtt_server(user,pwd):
	global client_edgex
	#client_edgex = mqtt_edgex.Client()
	client_edgex.username_pw_set(user,pwd)

	client_edgex.on_connect = on_connect
	client_edgex.on_message = on_message

	client_edgex.connect("10.112.122.28",1883,60)
	client_edgex.loop_start()


# ---------------------------------------------------------------------------
# This is a sample application package to publish sample device stats to
# IoTCC using MQTT protocol as DCC Comms
# User defined methods

def device_metric():
    global device_data
    _t = float(device_data)
    device_data = 0
    return _t

def http_req():
	 conn = httplib.HTTPConnection('localhost',47077,timeout=5)
    	 conn.request('GET', '/')
    	 res = conn.getresponse()
    	 data = res.read()
    	 data_dict = json.loads(data)
         addr = data_dict["addressable"]
	 user = addr["user"]
	 pwd = addr["password"]
	 topic = addr["topic"]
         filterr = data_dict["filter"]
         device_n = filterr["deviceIdentifiers"][0]
	 device_v = filterr["valueDescriptorIdentifiers"][0]
         global device_name
         global device_value_name
         global edgexmeta
         edgexmeta["topic"] = topic
	 device_name = device_n
	 device_value_name = device_v
	 mqtt_server(user,pwd)
	 conn.close()

class PackageClass(LiotaPackage):
    def run(self, registry):
        """
        The execution function of a liota package.
        Acquires "iotcc_mqtt" and "iotcc_mqtt_edge_system" from registry then register five devices
        and publishes device metrics to the DCC
        :param registry: the instance of ResourceRegistryPerPackage of the package
        :return:
        """
        http_req()
        from liota.entities.devices.device import Device
        from liota.entities.metrics.metric import Metric
        import copy

	global device_name
	global device_value_name
	log.info("-----------beging register device with:" + device_name + "--" +device_value_name)
        # Acquire resources from registry
        self.iotcc = registry.get("iotcc_mqtt")
        # Creating a copy of edge_system object to keep original object "clean"
        self.iotcc_edge_system = copy.copy(registry.get("iotcc_mqtt_edge_system"))

        self.reg_devices = []
        self.metrics = []

        try:
            # Register device

            device_01 = Device(device_name,systemUUID().get_uuid(device_name),"edgexfoundry")
            log.info("Registration Started for Device".format(device_01.name))

            # Device Registration

            reg_device_01 = self.iotcc.register(device_01)

            self.reg_devices.append(reg_device_01)
            self.iotcc.create_relationship(self.iotcc_edge_system, reg_device_01)

            # Use the device name as identifier in the registry to easily refer the device in other packages
            device_registry_name_01 = device_name
            registry.register(device_registry_name_01, reg_device_01)
	    log.info("----------------relation success:"+str(device_name)+"----------------------")
            self.iotcc.set_properties(reg_device_01,
                                              {"Country": "USA-G", "State": "California", "City": "Palo Alto",
                                               "Location": "VMware HQ", "Building": "Promontory H Lab",
                                               "Floor": "First Floor"})

            try:
                # Registering Metric for Devic
                metric_name_01 = device_value_name + "_metrics"

                metric_simulated_received_01 = Metric(name=metric_name_01, unit=None, interval=5,
                                                   aggregation_size=1, sampling_function=device_metric)
                reg_metric_simulated_received_01 = self.iotcc.register(metric_simulated_received_01)
                self.iotcc.create_relationship(reg_device_01, reg_metric_simulated_received_01)
                reg_metric_simulated_received_01.start_collecting()
		log.info("--------------relation metics:"+device_value_name+"----------------------")
                self.metrics.append(reg_metric_simulated_received_01)

            except Exception as e:
                log.error(
                    'Exception while lioading metric {0} for device {1} - {2}'.format(metric_name_01, device_01.name,
                                                                                     str(e)))

        except Exception:
            log.info("Device Registration and Metrics loading failed")
            raise

    def clean_up(self):
        """
        The clean up function of a liota package.
        Unregister Device and Stops metric collection
        :return:
        """
        # On the unload of the package the device will get unregistered and the entire history will be deleted
        # from Pulse IoT Control Center so comment the below logic if the unregsitration of the device is not required
        # to be done on the package unload
        for metric in self.metrics:
            metric.stop_collecting()
        for device in self.reg_devices:
            self.iotcc.unregister(device)
        log.info("Cleanup completed successfully")
