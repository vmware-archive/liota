from liota.entities.edgesystems.edgesystem import EdgeSystem
from liota.lib.utilities.utility import systemUUID


class Dk300EdgeSystem(EdgeSystem):

    def __init__(self, name):
        super(Dk300EdgeSystem, self).__init__(name=name, entity_id=systemUUID().get_uuid(name))
