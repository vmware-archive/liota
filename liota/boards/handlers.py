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

class ObjectConfig(object):
   """ Configuration Struct used for Gateway, physical and virtual Inputs/Outputs.

   """
   def __init__(self, identifier, name, local_identifier=None,
                uuid=None, res_kind=None, actions=None,
                stat_key=None, property_key_value_map=None, extra=None, ri=None, mi=None,
                direction=None, template=None, digital_pin=None,
                analog_pin=None, parent=None):
      # global unique identifier for Gateway
      self.identifier = identifier
      # only unique on this device
      self.local_identifier = local_identifier
      # uuid obtained by object registration from vROps
      self.uuid = uuid
      self.name = name
      self.res_kind = res_kind
      self.stat_key = stat_key
      self.property_key_value_map = property_key_value_map
      self.digital_pin = digital_pin
      self.analog_pin = analog_pin
      self.actions = actions
      self.parent = parent
      # extra data that can be associated with this object
      if extra is None:
         self.extra = {}
      else:
         self.extra = extra
      # response interval
      self.ri = ri
      # measurement interval
      self.mi = mi
      # direction (input/output)
      self.direction = direction
      # can be HelixGateway, HelixDigitalPin or HelixAnalogPin
      self.template = template

      # assert self.stat_key is not None or self.direction == "output" or self.template == "HelixGateway"
      # assert self.stat_key is not None
      assert self.identifier is not None and self.identifier != ""
      assert self.name is not None