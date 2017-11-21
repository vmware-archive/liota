import yaml

from liota.core.package_manager import LiotaPackage

class PackageClass(LiotaPackage):
    """
    This package contains specifications of GeneralEdgeSystem.
    It registers "edge system" in package manager's resource registry.
    """

    def run(self, registry):
        from liota.entities.edge_systems.general_edge_system import GeneralEdgeSystem

        # getting values from configuration file  
        configuration_file_name = registry.get("package_conf") + \
            '/user_packages/iotcv2/sampleProp.yml'
        with open(configuration_file_name, 'r') as stream:
            config = yaml.load(stream)

        # Initialize edgesystem
        edge_system = GeneralEdgeSystem(config['EdgeSystemName'])
        registry.register("edge_system", edge_system)

    def clean_up(self):
        pass
