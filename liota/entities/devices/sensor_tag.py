# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2015-2016 VMware, Inc. All Rights Reserved.                    #
#                                                                             #
#  Licensed under the BSD 2-Clause License (the “License”); you may not use   #
#  this file except in compliance with the License.                           #
#                                                                             #
#  The BSD 2-Clause License                                                   #
#                                                                             #
#  Redistribution and use in source and binary forms, with or without         #
#  modification, are permitted provided that the following conditions are met:#
#                                                                             #
#  - Redistributions of source code must retain the above copyright notice,   #
#      this list of conditions and the following disclaimer.                  #
#                                                                             #
#  - Redistributions in binary form must reproduce the above copyright        #
#      notice, this list of conditions and the following disclaimer in the    #
#      documentation and/or other materials provided with the distribution.   #
#                                                                             #
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"#
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE  #
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE #
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE  #
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR        #
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF       #
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS   #
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN    #
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)    #
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF     #
#  THE POSSIBILITY OF SUCH DAMAGE.                                            #
# ----------------------------------------------------------------------------#

import time
import Queue
import logging
import threading

from aenum import UniqueEnum
from bluepy.sensortag import SensorTag
from bluepy.btle import BTLEException

from liota.entities.devices.device import Device
from liota.lib.utilities.utility import systemUUID

log = logging.getLogger(__name__)


class Sensors(UniqueEnum):
    """
    Enum for sensors that can be enabled in a SensorTag Device.

    Note: Use ALL to enable all the sensors.
    """
    TEMPERATURE = 0
    HUMIDITY = 1
    BAROMETER = 2
    ACCELEROMETER = 3
    MAGNETOMETER = 4
    GYROSCOPE = 5
    LIGHTMETER = 6
    BATTERY_LEVEL = 7
    # All the above sensors
    ALL = 8


class SensorTagDevice(Device):
    """
    SensorTag Device Entity.

    Texas Instrument's SensorTag
    http://www.ti.com/ww/en/wireless_connectivity/sensortag2015/?INTC=SensorTag&HQS=sensortag

    This has helper thread implementation to connect with SensorTagDevice over BLE (Bluetooth Low Energy).  It
    facilitates collecting sensor metrics even in-case of dis-connectivity due to external factors, without any need
    of manual restart of the program.
    """

    def __init__(self, device_name, device_mac, entity_type="SensorTag",
                 sampling_interval_sec=10, retry_interval_sec=5, sensors=None):
        """
        :param device_name: SensorTag Device's name
        :param device_mac: SensorTag's MAC Address
        :param entity_type: EntityType of the device
        :param sampling_interval_sec: Time interval in seconds to collect metrics from sensors
        :param retry_interval_sec: Time interval in seconds to wait before attempting to retry establishing connection.
        :param sensors: List of Sensors to be enabled. Use Sensors Enum.
        """
        super(SensorTagDevice, self).__init__(
            name=device_name,
            entity_type=entity_type,
            entity_id=systemUUID().get_uuid(device_name)
        )

        self.tag = None
        self.device_name = device_name
        self.device_mac = device_mac
        self._sampling_interval_sec = sampling_interval_sec
        self._retry_interval_sec = retry_interval_sec
        # Flags to mark enabled Sensors
        self._temp_enabled = False
        self._humi_enabled = False
        self._baro_enabled = False
        self._acce_enabled = False
        self._magn_enabled = False
        self._gyro_enabled = False
        self._bat_level_enabled = False
        self._light_enabled = False

        if not isinstance(sensors, list) or len(sensors) == 0:
            log.error("List of sensors to be enabled is expected.")
            raise TypeError("List of sensors to be enabled is expected.")
        # List of sensors to be enabled
        self._enable_sensors_list = sensors
        self.start_collecting()

    def start_collecting(self):
        """
        Connects with SensorTag and starts helper thread for collecting metrics.
        :return: None
        """
        # To stop the thread
        self._is_running = True
        # Connects with re-try mechanism
        self._re_connect()
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()

    def _re_connect(self):
        """
        Reconnects with a SensorTag Device.

        Tries infinitely until connection is established successfully as BLE devices throw error frequently.
        :return: None
        """
        while self._is_running:
            # Wait for specified interval before attempting to re-connect
            time.sleep(self._retry_interval_sec)
            try:
                self._connect()
                # Break loop once connection is established successfully
                break
            except BTLEException as e:
                log.error(str(e))

    def _connect(self):
        """
        Connects with a SensorTag Device and enables the specified sensors.
        :return: None
        """
        log.info("Connecting to SensorTag Device: {0} with MAC_ADDRESS: {1}".format(self.device_name, self.device_mac))
        self.tag = SensorTag(addr=self.device_mac)
        log.info("Connected with SensorTag Device: {0} with MAC_ADDRESS: {1} Successfully!".
                 format(self.device_name, self.device_mac))
        # Enabling sensors once connection is successful
        self._enable()

    def _run(self):
        """
        Collects metrics from sensor in a single SensorTag Device and adds them to corresponding queue.

        In case of a dis-connectivity, it tries to re-connect automatically.
        :return: None
        """
        # Loop for auto-reconnect on device disconnect due to BTLEException
        while self._is_running:
            # Loop to read and collect metrics from enabled sensors
            while self._is_running:
                # Attempt reading from device with try-catch, as BTLEException occurs frequently
                try:
                    # isEnabled check for sensors
                    if self._temp_enabled:
                        self._temp_queue.put(self.tag.IRtemperature.read())

                    if self._humi_enabled:
                        self._humi_queue.put(self.tag.humidity.read())

                    if self._baro_enabled:
                        self._baro_queue.put(self.tag.barometer.read())

                    if self._acce_enabled:
                        self._acce_queue.put(self.tag.accelerometer.read())

                    if self._magn_enabled:
                        self._magn_queue.put(self.tag.magnetometer.read())

                    if self._gyro_enabled:
                        self._gyro_queue.put(self.tag.gyroscope.read())

                    if self._bat_level_enabled:
                        self._bat_level_queue.put(self.tag.battery.read())

                    if self._light_enabled:
                        self._light_queue.put(self.tag.lightmeter.read())

                    self.tag.waitForNotifications(self._sampling_interval_sec)
                except BTLEException as e:
                    log.error(str(e))
                    # Disconnecting on exception so that re-connect will be possible
                    self.tag.disconnect()
                    log.info("Disconnected with SensorTag Device: {0} with MAC_ADDRESS: {1} Successfully!".
                             format(self.device_name, self.device_mac))
                    break
            log.info("Attempting to re-connect")
            self._re_connect()

        log.info("Stopped SensorTagCollector Thread.")

    def stop_collecting(self):
        """
        Disconnect from SensorTag and stops the Thread.
        :return:
        """
        self._is_running = False
        # Wait for run() to stop to disconnect gracefully
        time.sleep(self._sampling_interval_sec)
        self.tag.disconnect()
        log.info("Disconnected with SensorTag Device: {0} with MAC_ADDRESS: {1} Successfully!".
                 format(self.device_name, self.device_mac))

    def _enable(self):
        """
        Enables specified sensors.
        :return: None
        """
        log.info("Enabling Sensors..")
        for sensor in self._enable_sensors_list:
            if sensor not in Sensors:
                log.error("Unsupported Sensor: {0}".format(sensor))
                raise TypeError("Unsupported Sensor: {0}".format(sensor))

            if sensor is Sensors.ALL:
                self._enable_temperature()
                self._enable_humidity()
                self._enable_barometer()
                self._enable_accelerometer()
                self._enable_magnetometer()
                self._enable_gyroscope()
                self._enable_battery_level()
                self._enable_lightmeter()

            elif sensor is Sensors.TEMPERATURE:
                self._enable_temperature()
            elif sensor is Sensors.HUMIDITY:
                self._enable_humidity()
            elif sensor is Sensors.BAROMETER:
                self._enable_barometer()
            elif sensor is Sensors.ACCELEROMETER:
                self._enable_accelerometer()
            elif sensor is Sensors.MAGNETOMETER:
                self._enable_magnetometer()
            elif sensor is Sensors.GYROSCOPE:
                self._enable_gyroscope()
            elif sensor is Sensors.BATTERY_LEVEL:
                self._enable_battery_level()
            elif sensor is Sensors.LIGHTMETER:
                self._enable_lightmeter()

        # Some sensors (e.g., temperature, accelerometer) need some time for initialization.
        # Not waiting here after enabling a sensor, the first read value might be empty or incorrect.
        time.sleep(2)

    def _enable_temperature(self):
        """
        Enables Temperature Sensor
        :return: None
        """
        if self.tag.IRtemperature is not None:
            self.tag.IRtemperature.enable()
            self._temp_enabled = True
            self._temp_queue = Queue.Queue()
            log.info("Enabled temperature sensor")
        else:
            log.error("Temperature sensor is not available in SensorTag Device: {0} with MAC_ADDRESS: {1}".
                      format(self.device_name, self.device_mac))

    def _enable_humidity(self):
        """
        Enables Humidity Sensor
        :return: None
        """
        if self.tag.humidity is not None:
            self.tag.humidity.enable()
            self._humi_enabled = True
            self._humi_queue = Queue.Queue()
            log.info("Enabled humidity sensor")
        else:
            log.error("Humidity sensor is not available in SensorTag Device: {0} with MAC_ADDRESS: {1}".
                      format(self.device_name, self.device_mac))

    def _enable_barometer(self):
        """
        Enables Barometer
        :return: None
        """
        if self.tag.barometer is not None:
            self.tag.barometer.enable()
            self._baro_enabled = True
            self._baro_queue = Queue.Queue()
            log.info("Enabled barometer")
        else:
            log.error("Barometer is not available in SensorTag Device: {0} with MAC_ADDRESS: {1}".
                      format(self.device_name, self.device_mac))

    def _enable_accelerometer(self):
        """
        Enables Accelerometer
        :return: None
        """
        if self.tag.accelerometer is not None:
            self.tag.accelerometer.enable()
            self._acce_enabled = True
            self._acce_queue = Queue.Queue()
            log.info("Enabled accelerometer")
        else:
            log.error("Accelerometer is not available in SensorTag Device: {0} with MAC_ADDRESS: {1}".
                      format(self.device_name, self.device_mac))

    def _enable_magnetometer(self):
        """
        Enables Magnetometer
        :return: None
        """
        if self.tag.magnetometer is not None:
            self.tag.magnetometer.enable()
            self._magn_enabled = True
            self._magn_queue = Queue.Queue()
            log.info("Enabled magnetometer")
        else:
            log.error("Magnetometer is not available in SensorTag Device: {0} with MAC_ADDRESS: {1}".
                      format(self.device_name, self.device_mac))

    def _enable_gyroscope(self):
        """
        Enables Gyroscope
        :return: None
        """
        if self.tag.gyroscope is not None:
            self.tag.gyroscope.enable()
            self._gyro_enabled = True
            self._gyro_queue = Queue.Queue()
            log.info("Enabled gyroscope")
        else:
            log.error("Gyroscope is not available in SensorTag Device: {0} with MAC_ADDRESS: {1}".
                      format(self.device_name, self.device_mac))

    def _enable_battery_level(self):
        """
        Enables battery level
        :return: None
        """
        if self.tag.battery is not None:
            self.tag.battery.enable()
            self._bat_level_enabled = True
            self._bat_level_queue = Queue.Queue()
            log.info("Enabled battery level")
        else:
            log.error("Battery level is not available in SensorTag Device: {0} with MAC_ADDRESS: {1}".
                      format(self.device_name, self.device_mac))

    def _enable_lightmeter(self):
        """
        Enables Light sensor
        :return: None
        """
        if self.tag.lightmeter is not None:
            self.tag.lightmeter.enable()
            self._light_enabled = True
            self._light_queue = Queue.Queue()
            log.info("Enabled lightmeter")
        else:
            log.error("lightmeter is not available in SensorTag Device: {0} with MAC_ADDRESS: {1}".
                      format(self.device_name, self.device_mac))

    def get_sensor_tag(self):
        """
        Returns SensorTagDevice entity.
        :return: SensorTagDevice entity object.
        """
        return self.tag

    def get_temperature(self):
        """
        Blocks until (sampling_interval_sec + 1 sec); returns None otherwise
        :return: (ambient_temp, target_temp) tuple in degC
        """
        try:
            return self._temp_queue.get(True, self._sampling_interval_sec + 1)
        except Queue.Empty:
            # Not raising exception as it occurs due to BLE exception as device disconnects frequently
            log.error("temperature not collected from SensorTag..")
            return None
        except Exception as e:
            log.exception("temperature error traceback..")
            raise e

    def get_humidity(self):
        """
        Blocks until (sampling_interval_sec + 1 sec); returns None otherwise
        :return: (ambient_temp, rel_humidity) tuple
        """
        try:
            return self._humi_queue.get(True, self._sampling_interval_sec + 1)
        except Queue.Empty:
            # Not raising exception as it occurs due to BLE exception as device disconnects frequently
            log.error("humidity not collected from SensorTag..")
            return None
        except Exception as e:
            log.exception("humidity error traceback..")
            raise e

    def get_barometer(self):
        """
        Blocks until (sampling_interval_sec + 1 sec); returns None otherwise
        :return: (ambient_temp in degC, pressure in millibars) tuple
        """
        try:
            return self._baro_queue.get(True, self._sampling_interval_sec + 1)
        except Queue.Empty:
            # Not raising exception as it occurs due to BLE exception as device disconnects frequently
            log.error("barometer not collected from SensorTag..")
            return None
        except Exception as e:
            log.exception("barometer error traceback..")
            raise e

    def get_accelerometer(self):
        """
        Blocks until (sampling_interval_sec + 1 sec); returns None otherwise
        :return: (x_accel, y_accel, z_accel) tuple in units of g
        """
        try:
            return self._acce_queue.get(True, self._sampling_interval_sec + 1)
        except Queue.Empty:
            # Not raising exception as it occurs due to BLE exception as device disconnects frequently
            log.error("accelerometer not collected from SensorTag..")
            return None
        except Exception as e:
            log.exception("accelerometer error traceback..")
            raise e

    def get_magnetometer(self):
        """
        Blocks until (sampling_interval_sec + 1 sec); returns None otherwise
        :return: (x_mag, y_mag, z_mag) in units of uT
        """
        try:
            return self._magn_queue.get(True, self._sampling_interval_sec + 1)
        except Queue.Empty:
            # Not raising exception as it occurs due to BLE exception as device disconnects frequently
            log.error("magnetometer not collected from SensorTag..")
            return None
        except Exception as e:
            log.exception("magnetometer error traceback..")
            raise e

    def get_gyroscope(self):
        """
        Blocks until (sampling_interval_sec + 1 sec); returns None otherwise
        :return: (x_gyro, y_gyro, z_gyro) tple in units of degrees/sec
        """
        try:
            return self._gyro_queue.get(True, self._sampling_interval_sec + 1)
        except Queue.Empty:
            # Not raising exception as it occurs due to BLE exception as device disconnects frequently
            log.error("gyroscope not collected from SensorTag..")
            return None
        except Exception as e:
            log.exception("gyroscope error traceback..")
            raise e

    def get_battery_level(self):
        """
        Blocks until (sampling_interval_sec + 1 sec); returns None otherwise
        :return: battery level in percent
        """
        try:
            return self._bat_level_queue.get(True, self._sampling_interval_sec + 1)
        except Queue.Empty:
            # Not raising exception as it occurs due to BLE exception as device disconnects frequently
            log.error("battery_level not collected from SensorTag..")
            return None
        except Exception as e:
            log.exception("battery_level error traceback..")
            raise e

    def get_light_level(self):
        """
        Blocks until (sampling_interval_sec + 1 sec); returns None otherwise
        :return: value in lux
        """
        try:
            return self._light_queue.get(True, self._sampling_interval_sec + 1)
        except Queue.Empty:
            # Not raising exception as it occurs due to BLE exception as device disconnects frequently
            log.error("light_level not collected from SensorTag..")
            return None
        except Exception as e:
            log.exception("light_level error traceback..")
            raise e
