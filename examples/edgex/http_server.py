from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import SocketServer
import json
import random
import threading
import os

import mqtt_server


class S(BaseHTTPRequestHandler):
	edgexcache = ''
	def _set_headers(self):
		self.send_response(200)
		self.send_header('Content-type','application/json')
		self.end_headers()
	def do_GET(self):
		self._set_headers()
                self.wfile.write(S.edgexcache)
		print("edgexcache: " +S.edgexcache)
	def do_HEAD(self):
		self._set_headers()
	def do_POST(self):
		self._set_headers()
		print("----post request handler")
		self.data_string = self.rfile.read(int(self.headers['Content-Length']))
		self.send_response(200)
		self.end_headers()

		data = json.loads(self.data_string)
		mq_info = data["addressable"]
		user = mq_info["user"]
		pwd = mq_info["password"]
		topic = mq_info["topic"]
		filterr = data["filter"]
		device_n = filterr["deviceIdentifiers"][0]
		device_v = filterr["valueDescriptorIdentifiers"][0]

		mqtt_server.mq_user = mq_info["user"]
		mqtt_server.mq_pwd = mq_info["password"]
		mqtt_server.mq_topic = mq_info["topic"]
		mqtt_server.run()
		print("mqtt_server has started.....")
		S.edgexcache = self.data_string
		p = os.popen("/usr/bin/sha1sum /usr/lib/liota/packages/device_add_template.py | awk '{print $1}'")
		result = p.read()
		os.system("/usr/lib/liota/packages/liotad/liotapkg.sh  load  device_add_template " + result)
		p.close()
		self.wfile.write("success.")

def run(server_class=HTTPServer,handler_class=S,port=47077):

	httpd = server_class(("",port),handler_class)
	print("start http server on port " + str(port) +"...")
	http_d = threading.Thread(name='http_server',target=httpd.serve_forever)
	http_d.daemon = True
	http_d.start()
	print("after started...")

if __name__ == "__main__":
	run()
#else:
#	run()

print("in http server#############")
