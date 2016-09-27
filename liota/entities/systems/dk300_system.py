from system import System
from liota.utilities.utility import systemUUID


class Dk300System(System):

    def __init__(self, name):
        super(Dk300System, self).__init__(name=name, entity_id=systemUUID().get_uuid(name))
