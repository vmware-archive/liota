import time
from cpppo.server.enip import client
from cpppo.server.enip.getattr import attribute_operations
import json

HOST = "host"


with client.connector(host=HOST) as conn:
        i = 1 
        while(1):
        	try:
                data = [int(i) for c in range( 1 )]
                elements = len (data)
			    tag_type = client.enip.DINT.tag_type
			    tag = "Scada"
			    req = conn.write( tag, elements=elements, data=data,
                              tag_type=tag_type)
        
        	except AssertionError:
                	print "Response timed out!! Tearing Connection and Reconnecting!!!!!"
        	except socket.error as exc:
                	print "Couldn't send command: %s" 
		
		time.sleep(5)
		i = i + 1


