Integrate Kura into Liota

Kura aims at offering a Java/OSGi-based container for M2M applications running in service gateways. Kura provides or, when available, aggregates open source implementations for the most common services needed by M2M applications. Kura components are designed as configurable OSGi Declarative Service exposing service API and raising events. While several Kura components are in pure Java, others are invoked through JNI and have a dependency on the Linux operating system.So it’s worth explore how to integrate this into Liota. 

This directory includes:
File 1: kura_integrate_iotcc.py


How to use it:

1.sha1sum kura_integrate_iotcc.py --> 16013ef7a95f59537bc5ab1d91a5c599c9cb8ab4
2.liotapkg.sh load kura_integrate_iotcc 16013ef7a95f59537bc5ab1d91a5c599c9cb8ab4
3.config Kura UI to publish data

How to use Kura UI:
1.Create local mqtt connection, please refer: https://esf.eurotech.com/docs/configure-everyware-cloud-connection
2.Create wires, please refer: https://esf.eurotech.com/docs/kura-wires-overview
3.Use wires to publish data to local mqtt broker.

the kura_integrate_iotcc.py will auto add sensor.