from liota.dccs.iotcv2 import Iotcv2
from liota.lib.utilities.utility import read_user_config
from liota.dccs.dcc import RegistrationFailure, SetPropertiesFailure
from liota.core.package_manager import LiotaPackage
from liota.lib.utilities.identity import Identity
from liota.dcc_comms.mqtt_dcc_comms import MqttDccComms
from liota.lib.utilities.tls_conf import TLSConf
import logging
import os

log = logging.getLogger(__name__)

dependencies = []

class PackageClass(LiotaPackage):
    """
    This package creates a IoTCV2 DCC object, registers Toyota edge system (TES),
    sets its properties, register 19 ECUs, sets theirs properties, and creates
    relationships between TES and ECUs on IoTCV2
    """

    def run(self, registry):
        from liota.entities.edge_systems.general_edge_system import GeneralEdgeSystem
        from liota.entities.devices.simulated_device import SimulatedDevice

        # Get values from configuration file
        config_path = registry.get("package_conf")
        self.config = read_user_config(config_path + '/user_packages/iotcv2/sampleProp.conf')

        # Initialize edgesystem
        edge_system = GeneralEdgeSystem(os.environ['VIN'])
        registry.register("edge_system", edge_system)

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
            return
        try:
            self.iotcc.set_properties(self.iotcc_edge_system, self.config['EdgeSystemPropList'])
        except SetPropertiesFailure:
            print "EdgeSystem setting properties failed"

        # Register 19 ECU devices
        self.reg_ecus = []
        ecu_makes = ["Bosch", "Denso", "FujitsuTEN"]
        ecu_models = [["BAEX1", "BWE2X", "BYTSE01", "BGGUTE22", "BFF1"], \
                     ["DAEX1", "DWE2X", "DYTSE01", "DGGUTE22", "DFF1"], \
                     ["FAEX1", "FWE2X", "FYTSE01", "FGGUTE22", "FFF1"]]
        num_ecus = 19
        try:
            for i in range(0, num_ecus):
                # Register device
                log.info("*****Registeration Started for ECU %s" %(i))
                ecu = SimulatedDevice(self.config['ECUNameList'][i] + '-' + os.environ['VIN'], "Toyota-ECU")
                self.reg_ecu = self.iotcc.register(ecu)
                self.reg_ecus.append(self.reg_ecu)
                # create full ECU proplist
                ecu_sn = '%0*d' % (12, (int(os.environ['MO_SN_START']) + i))
                log.debug("ecu_sn:{0} PropList:{1}".format(ecu_sn, self.config['ECUPropList']))
                prop_dict = {}
                prop_dict.update({"Make": ecu_makes[i % 3]})
                prop_dict.update({"Model": ecu_models[i % 3][i % 5]})
                prop_dict.update({"SerialNumber": ecu_sn})
                log.debug("new PropList:{0}".format(prop_dict))
                self.iotcc.set_properties(self.reg_ecu, prop_dict)
                self.iotcc.create_relationship(self.iotcc_edge_system, self.reg_ecu)
        except Exception:
            log.exception("Connected Device Registration and Metrics are Not Available")

    def clean_up(self):
        """
        for ecu in self.reg_ecus:
            self.iotcc.unregister(ecu)
        """
        self.iotcc.comms.client.disconnect()


