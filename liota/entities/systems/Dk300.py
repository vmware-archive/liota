from system import System
from liota.utilities.utility import systemUUID


class Dk300(System):

    def __init__(self, name):
        super(Dk300 ,self).__init__(name=name, entity_id=systemUUID().get_uuid(name))

    def send_data(self):
        print "Send Values"