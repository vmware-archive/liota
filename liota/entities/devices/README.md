# Devices (Things)

Similar to Edge Systems, Devices are also an Entity in LIOTA.  This python package consists of modules so that LIOTA agent in an Edge System
can connect with devices and collect metrics at ease.

Currently, following devices are supported.

## Simulated Device

This is used to showcase LIOTA's capability in simulated environments.

## Texas Instrument's SensorTag

Python [bluepy](https://github.com/IanHarvey/bluepy) module is used to connect with SensorTag over BLE (Bluetooth Low Energy).  This requires a pre-requisite to be installed
as mentioned in its documentation.

```
$ sudo apt-get install libglib2.0-dev
```

Install this prerequisite before trying out liota-sensor-tag examples.
