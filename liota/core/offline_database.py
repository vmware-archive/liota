# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2015-2016 VMware, Inc. All Rights Reserved.                    #
#                                                                             #
#  Licensed under the BSD 2-Clause License (the “License”); you may not use   #
#  this file except in compliance with the License.                           #
#                                                                             #
#  The BSD 2-Clause License                                                   #
#                                                                             #
#  Redistribution and use in source and binary forms, with or without         #
#  modification, are permitted provided that the following conditions are met:#
#                                                                             #
#  - Redistributions of source code must retain the above copyright notice,   #
#      this list of conditions and the following disclaimer.                  #
#                                                                             #
#  - Redistributions in binary form must reproduce the above copyright        #
#      notice, this list of conditions and the following disclaimer in the    #
#      documentation and/or other materials provided with the distribution.   #
#                                                                             #
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"#
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE  #
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE #
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE  #
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR        #
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF       #
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS   #
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN    #
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)    #
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF     #
#  THE POSSIBILITY OF SUCH DAMAGE.                                            #
# ----------------------------------------------------------------------------#

import logging
import sqlite3
import threading
import time
from liota.dcc_comms.dcc_comms import DCCComms
from liota.dcc_comms.check_connection import CheckConnection

log = logging.getLogger(__name__)

class OfflineDatabase:
	def __init__(self, table_name, comms, conn=None, data_drain_size=1, draining_frequency=0):
		"""
			:param table_name: table_name in which message will be stored
			:param comms: comms instance of DCCComms
			:param data_drain_size: how many messages will be drained within each draining_frequency secs defined.
			:param draining_frequency: frequency with which data will be published after internet connectivity established(like seconds).
		"""
		if not isinstance(table_name, basestring):
			log.error("Table name should be a string.")
			raise TypeError("Table name should be a string.")
		if not isinstance(comms, DCCComms):
			log.error("DCCComms object is expected.")
			raise TypeError("DCCComms object is expected.")
		if not isinstance(draining_frequency, float) and not isinstance(draining_frequency, int):
			log.error("draining_frequency is expected of float or int type.")
			raise TypeError("draining_frequency is expected of float or int type.")
		try: 
			assert draining_frequency>=0
		except AssertionError as e:
			log.error("draining_frequency can't be negative.")
			raise e("draining_frequency can't be negative.")
		self.table_name = table_name
		if conn is None:
			self.internet_conn = CheckConnection()
		else:
			self.internet_conn = conn
		self.draining_frequency = draining_frequency
		self.data_drain_size = data_drain_size
		self.comms = comms
		self.flag_conn_open = False
		self.draining_in_progress = False
		self._offline_db_lock = threading.Lock()
		self._create_table()

	def _create_table(self):
		if self.flag_conn_open is False:
			self.conn = sqlite3.connect('storage.db')
			try:
				with self.conn:
					if not self.conn.execute("SELECT name FROM sqlite_master WHERE TYPE='table' AND name= ? ", (self.table_name,)).fetchone():
						self.conn.text_factory = str
						self.flag_conn_open = True
						self.cursor = self.conn.cursor()
						self.cursor.execute("CREATE TABLE "+self.table_name+" (Message TEXT)")
						self.cursor.close()
						del self.cursor
					else:
						 log.info("Table already there!!!")
			except Exception as e:
				raise e
			finally:
				self.flag_conn_open = False
				self.conn.close()

	def add(self, message):
		try:
			self.conn = sqlite3.connect('storage.db')
			self.flag_conn_open = True
			with self.conn:
				self.cursor = self.conn.cursor()
				log.info("Adding data to "+ self.table_name)
				self.cursor.execute("INSERT INTO "+self.table_name+"(Message) VALUES (?);", (message,))
				self.cursor.close()
				del self.cursor
		except sqlite3.OperationalError as e:
			raise e
		finally:
			self.conn.close()
			self.flag_conn_open = False

	def _drain(self):
		self._offline_db_lock.acquire()
		self.conn = sqlite3.connect('storage.db')
		self.flag_conn_open = True
		self.draining_in_progress = True
		self.cursor = self.conn.cursor()
		self.del_cursor = self.conn.cursor()
		data_drained = 0
		try:
			for row in self.cursor.execute("SELECT Message FROM "+self.table_name):
				if self.comms is not None and self.internet_conn.check :
					try:
						self.comms.send(row[0])
						log.info("Data Drain: {}".format(row[0]))
						data_drained+=1
						self.del_cursor.execute("Delete from "+self.table_name+" where rowid IN (Select rowid from "+self.table_name+" limit 1);")
						self.conn.commit()
					except Exception as e:
						raise e
				else:						#internet connectivity breaks while draining
					log.warning("Internet broke while draining")
					break
				if data_drained==self.data_drain_size:		#if some amt. of data drained thread sleeps for specified draining_freqn.
					data_drained=0
					time.sleep(self.draining_frequency)
		except Exception as e:
			raise e
			log.warning("Internet connectivity broke while draining.")
		finally:
			self.del_cursor.close()
			del self.del_cursor
			self.conn.close()
			self.flag_conn_open = False	
			self.draining_in_progress = False	
		self._offline_db_lock.release()

	def start_drain(self):
		queueDrain = threading.Thread(target=self._drain)
		queueDrain.daemon = True
		queueDrain.start()
