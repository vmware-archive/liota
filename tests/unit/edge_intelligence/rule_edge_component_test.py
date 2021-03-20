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

import unittest
from liota.edge_component.rule_edge_component import RuleEdgeComponent

def actuator_udm():
	pass

ModelRule = lambda rpm : 1 if (rpm>=rpm_limit) else 0
exceed_limit = 1

class TestRuleEdgeComponent(unittest.TestCase):
	
	def test_RuleEdgeComponent_fail_without_valid_modelRule(self):
		#Fails if no argument pass
		with self.assertRaises(Exception):
			edge_component = RuleEdgeComponent()
			assertNotIsInstance(edge_component, RuleEdgeComponent)
		
		#Fails if not valid Model rule passed
		with self.assertRaises(Exception):
			edge_component = RuleEdgeComponent("asd", exceed_limit, actuator_udm)
			assertNotIsInstance(edge_component, RuleEdgeComponent)

		#Fails if lambda function not passed as ModelRule
		with self.assertRaises(Exception):
			edge_component = RuleEdgeComponent(actuator_udm, exceed_limit, actuator_udm)
			assertNotIsInstance(edge_component, RuleEdgeComponent)

	def test_RuleEdgeComponent_takes_valid_modelRule(self):
		edge_component = RuleEdgeComponent(ModelRule, exceed_limit, actuator_udm)
		assert isinstance(edge_component, RuleEdgeComponent)

	def test_RuleEdgeComponent_fail_with_invalidArg_exceedLimit(self):
		#Fails if int not passed as exceed_limit
		with self.assertRaises(Exception):
			edge_component = RuleEdgeComponent(ModelRule, 2.0, actuator_udm)
			assertNotIsInstance(edge_component, RuleEdgeComponent)

	def test_RuleEdgeComponent_takes_validArg_exceedLimit(self):
		edge_component = RuleEdgeComponent(ModelRule, exceed_limit, actuator_udm)
		assert isinstance(edge_component, RuleEdgeComponent)

	def test_RuleEdgeComponent_fails_without_valid_actionActuator(self):
		#Fails if actuator_udm not of function type
		with self.assertRaises(Exception):
			edge_component = RuleEdgeComponent(ModelRule, exceed_limit, "asd")
			assertNotIsInstance(edge_component, RuleEdgeComponent)

	def test_RuleEdgeComponent_takes_valid_actionActuator(self):
		edge_component = RuleEdgeComponent(ModelRule, exceed_limit, actuator_udm)
		assert isinstance(edge_component, RuleEdgeComponent)

if __name__ == '__main__':
	unittest.main()
