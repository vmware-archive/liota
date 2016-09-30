from liota.entities.edge_systems.edge_system import EdgeSystem
from liota.lib.utilities.utility import systemUUID


class Dk300EdgeSystem(EdgeSystem):

    def __init__(self, name):
        super(Dk300EdgeSystem, self).__init__(name=name, entity_id=systemUUID().get_uuid(name))
