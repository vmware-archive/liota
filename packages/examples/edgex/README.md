# EdgexFoundry and Pulse integration through liota.

Integrate EdgeXFoundry into Liota

As the Open Interop Platform for the IoT Edge, EdgeX Foundry™, https://www.edgexfoundry.org/, is a vendor-neutral open source project building a common open framework for IoT edge computing. At the heart of the project is an interoperability framework hosted within a full hardware- and OS-agnostic reference software platform to enable an ecosystem of plug-and-play components that unifies the marketplace and accelerates the deployment of IoT solutions. So it’s worth explore how to integrate this into Liota.

This directory includes:
File 1: edgex_device.py

## How to run edgexfoundry
https://github.com/edgexfoundry/edgex-go/blob/master/docs/getting-started/Ch-GettingStartedUsers.rst

## How to use
```
cp edgex_device.py /usr/lib/liota/packages/

sudo /usr/lib/liota/packages/liotad/liotapkg.sh load  \
examples/mqtt/iotcc/edgex_device  \
`sha1sum  /etc/liota/packages/examples/edgex_device.py | awk '{print \$1}'` \
```
