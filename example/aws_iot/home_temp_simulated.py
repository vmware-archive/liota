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


from liota.dcc.aws_iot import AWSIoT
from liota.identity.gateway_identity import Identity
from liota.boards.gateway_dk300 import Dk300
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import random

# getting values from conf file
config = {}
execfile('../sampleProp.conf', config)


# Random number generator, simulating living room temperature readings.
def living_room_temperature():
    return random.randint(10, 30)


# Random number generator, simulating kitchen temperature readings.
def kitchen_temperature():
    return random.randint(10, 30)


# Random number generator, simulating bedroom temperature readings.
def bedroom_temperature():
    return random.randint(10, 30)


if __name__ == '__main__':
    gateway = Dk300(config['Gateway1Name'])

    #  Using Identity layer for holding details related to authentication
    identity = Identity(config['RootCAPath'], config['ClientCertPath'], config['PrivateKeyPath'], None, None)

    #  Connecting to AWS
    #  These are standard steps to follow to connect with AWS IoT using AWS IoT SDK
    mqtt_client = AWSIoTMQTTClient(config['ClientName'])
    mqtt_client.configureEndpoint(config['AWSEndpoint'], config['AWSPort'])
    mqtt_client.configureCredentials(identity.cacert, identity.keyfile, identity.certfile)
    mqtt_client.configureConnectDisconnectTimeout(config['ConnectDisconnectTimeout'])
    mqtt_client.configureMQTTOperationTimeout(config['OperationTimeout'])
    mqtt_client.connect()
    print "Connected to AWS !"

    #  Initializing AWS DCC using AWSIoT client object
    aws = AWSIoT(mqtt_client)
    #  Registering Gateway
    aws_gateway = aws.register(gateway)

    #  Creating messaging_attributes to publish living room temperature
    #  QoS is 1 by default
    living_room_mess_attr = aws.create_messaging_attributes(config['LivingRoomPublishTopic'])  # Publish topic
    #  Creating metric
    living_room_metric = aws.create_metric(aws_gateway, "Living Room Temperature", "Celsius", sampling_interval_sec=5,
                                          aggregation_size=1, sampling_function=living_room_temperature,
                                          messaging_attributes=living_room_mess_attr)
    #  Publishing data to AWS based on created Metric
    living_room_metric.start_collecting()

    #  Similarly for kitchen
    kitchen_mess_attr = aws.create_messaging_attributes(config['KitchenPublishTopic'])
    kitchen_metric = aws.create_metric(aws_gateway, "Kitchen Temperature", "Celsius", sampling_interval_sec=5,
                                          aggregation_size=1, sampling_function=kitchen_temperature,
                                          messaging_attributes=kitchen_mess_attr)
    kitchen_metric.start_collecting()

    # Similarly for bedroom
    bedroom_mess_attr = aws.create_messaging_attributes(config['BedroomPublishTopic'])
    bedroom_metric = aws.create_metric(aws_gateway, "Bedroom Temperature", "Celsius", sampling_interval_sec=5,
                                       aggregation_size=1, sampling_function=bedroom_temperature,
                                       messaging_attributes=bedroom_mess_attr)
    bedroom_metric.start_collecting()





