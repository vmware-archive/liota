from system import System
from liota.utilities.utility import systemUUID


class Dk50(System):

    # def send_data(self):
    #      print "cannot publish values"

    def sample(self, name):
        super(Dk50 ,self).__init__(self, name=name, entity_id=systemUUID().get_uuid(name))


