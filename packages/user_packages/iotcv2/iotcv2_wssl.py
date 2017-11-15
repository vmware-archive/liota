import yaml

from liota.dccs.iotcv2 import Iotcv2
from liota.dccs.dcc import RegistrationFailure
from liota.core.package_manager import LiotaPackage
from liota.lib.utilities.identity import Identity
from liota.dcc_comms.mqtt_dcc_comms import MqttDccComms
from liota.lib.utilities.tls_conf import TLSConf

dependencies = ["user_packages/iotcv2/iotcv2_edge_system"]

class PackageClass(LiotaPackage):
    """
    This package creates a IoTCV2 DCC object and registers edge system on IoTCV2
    """

    def run(self, registry):
        import copy

        # Get values from configuration file
        configuration_file_name = registry.get("package_conf") + \
            '/user_packages/iotcv2/sampleProp.yml'
        with open(configuration_file_name, 'r') as stream:
            self.config = yaml.load(stream)

        # Acquire resources from registry
        # Creating a copy of edge_system object to keep original object "clean"
        edge_system = copy.copy(registry.get("edge_system"))

        # Encapsulate Identity
        identity = Identity(root_ca_cert=self.config['broker_root_ca_cert'],
                            username=self.config['broker_username'],
                            password=self.config['broker_password'],
                            cert_file=None, #self.config['edge_system_cert_file'],
                            key_file=None #self.config['edge_system_key_file']
                           )

        tls_conf = TLSConf(self.config['cert_required'],
                           self.config['tls_version'], None)

        # Initialize DCC object with MQTT transport
        self.iotcc = Iotcv2(
                                      MqttDccComms(edge_system_name=edge_system.name,
                                                   url=self.config['BrokerIP'],
                                                   port=self.config['BrokerPort'],
                                                   identity=identity,
                                                   tls_conf=tls_conf,
                                                   enable_authentication=True
                                                   )
                                      )
        try:
            self.iotcc_edge_system = self.iotcc.register(edge_system)
            registry.register("iotc_v2_mqtt_wssl", self.iotcc)
            registry.register("iotc_v2_mqtt_wssl_edge_system", self.iotcc_edge_system)
        except RegistrationFailure:
            print "EdgeSystem registration to IOTCV2 failed"
        #self.iotcc.set_properties(self.iotcc_edge_system,{"key1": "value1", "key2": "value2"})

    def clean_up(self):
        #Unregister edge system
        if self.config['ShouldUnregisterOnUnload'] == "True":
            self.iotcc.unregister(self.iotcc_edge_system)
        self.iotcc.comms.client.disconnect()


