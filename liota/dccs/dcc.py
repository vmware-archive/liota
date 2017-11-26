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
import json
from abc import ABCMeta, abstractmethod

from liota.entities.entity import Entity
from liota.dcc_comms.dcc_comms import DCCComms
from liota.entities.metrics.registered_metric import RegisteredMetric
from liota.dcc_comms.check_connection import CheckConnection
from liota.core.offline_queue import OfflineQueue
from liota.core.offline_database import OfflineDatabase
from liota.lib.utilities.offline_buffering import BufferingParams

log = logging.getLogger(__name__)

class DataCenterComponent:
    """
    Abstract base class for all DCCs.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, comms, buffering_params):
        if not isinstance(comms, DCCComms):
            log.error("DCCComms object is expected.")
            raise TypeError("DCCComms object is expected.")
        self.comms = comms
        self.buffering_params = buffering_params
        if self.buffering_params is not None:
            self.persistent_storage = self.buffering_params.persistent_storage
            self.data_drain_size = self.buffering_params.data_drain_size
            self.draining_frequency = self.buffering_params.draining_frequency
            self.drop_oldest = self.buffering_params.drop_oldest
            self.queue_size = self.buffering_params.queue_size
            self.conn = CheckConnection()
            self.offline_buffering_enabled = False         #False means offline buffering/storage is off else on

    # -----------------------------------------------------------------------
    # Implement this method in subclasses and do actual registration.
    #
    # This method should return a RegisteredEntity if successful, or raise
    # an exception if failed. Call this method from subclasses for a type
    # check.
    #

    @abstractmethod
    def register(self, entity_obj):
        if not isinstance(entity_obj, Entity):
            log.error("Entity object is expected.")
            raise TypeError("Entity object is expected.")

    @abstractmethod
    def create_relationship(self, reg_entity_parent, reg_entity_child):
        pass

    @abstractmethod
    def _format_data(self, reg_metric):
        pass

    def publish(self, reg_metric):
        if not isinstance(reg_metric, RegisteredMetric):
            log.error("RegisteredMetric object is expected.")
            raise TypeError("RegisteredMetric object is expected.")
        
        message = self._format_data(reg_metric)
        if message is not None:
            if self.buffering_params is not None:
                if self.conn.check:
                    if self.offline_buffering_enabled:         #checking if buffering is enabled or not, incase internet comes back after disconnectivity
                        self.offline_buffering_enabled = False
                        if self.persistent_storage is True:
                            log.info("Draining starts.")
                            self.offline_database.start_drain()
                        else:
                            self.offlineQ.start_drain()    
                    try:
                        if hasattr(reg_metric, 'msg_attr'):
                            self.comms.send(message, reg_metric.msg_attr)   
                        else:
                            self.comms.send(message, None)
                    except Exception as e:
                        raise e
                else:                                       #if no internet connectivity
                    if self.persistent_storage is True:
                        table_name = self.__class__.__name__ + type(self.comms).__name__
                        self._start_database_storage(table_name, message)
                    else:
                        self._start_queuing(message)
            else:
                if hasattr(reg_metric, 'msg_attr'):
                    self.comms.send(message, reg_metric.msg_attr)
                else:
                    self.comms.send(message, None)
                
    def _start_queuing(self, message):
        if self.offline_buffering_enabled  is False:
            self.offline_buffering_enabled = True
            try:
                if self.offlineQ.draining_in_progress:
                    self.offlineQ.append(message)
            except Exception as e:
                self.offlineQ = OfflineQueue(comms=self.comms, conn=self.conn, queue_size=self.queue_size,
                                data_drain_size=self.data_drain_size, drop_oldest=self.drop_oldest, 
                                draining_frequency=self.draining_frequency)
                log.info("Offline queueing started.") 
        self.offlineQ.append(message)

    def _start_database_storage(self, table_name, message):
        if self.offline_buffering_enabled  is False:
            self.offline_buffering_enabled = True
            try:
                if self.offline_database.draining_in_progress:
                    self.offline_database.add(message)
            except Exception as e:
                self.offline_database = OfflineDatabase(table_name=table_name, comms=self.comms, conn=self.conn, 
                                    data_drain_size=self.data_drain_size, draining_frequency=self.draining_frequency)
                log.info("Database created.")
                self.offline_database.add(message)
        else:
            self.offline_database.add(message)   

    @abstractmethod
    def set_properties(self, reg_entity, properties):
        pass

    @abstractmethod
    def unregister(self, entity_obj):
        if not isinstance(entity_obj, Entity):
            raise TypeError

class RegistrationFailure(Exception): 
    pass
