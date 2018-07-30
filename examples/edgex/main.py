import time
import mqtt_server

def test():
	print("test----------!")
	http_server.run()
	print("after call http server....")
	while (1 > 0 ):
	     time.sleep(3)
	     print("main test...." + str(mqtt_server.edgex_data))
	    # conn = sqlite3.connect(':memory:')
            # cur = conn.cursor()
            # cur.execute('select * from regist_info')
            # print cur.fetchall()
	    # conn.close()
test()
