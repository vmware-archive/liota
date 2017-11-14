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
from liota.edge_component.tensorflow_edge_component import TensorFlowEdgeComponent

def actuator_udm():
	pass

ModelPath = "ModelPath"

class TestTensorFlowEdgeComponent(unittest.TestCase):
	
	def test_TensorFlowEdgeComponent_fails_without_valid_ModelPath(self):
		with self.assertRaises(Exception):
			edge_component = TensorFlowEdgeComponent("/home/asd", actuator_udm)
			assertNotIsInstance(edge_component, TensorFlowEdgeComponent)

	def test_TensorFlowEdgeComponent_pass_with_valid_ModelPath(self):
		with self.assertRaises(Exception):
			edge_component = TensorFlowEdgeComponent(ModelPath, actuator_udm)
			assert isInstance(edge_component, TensorFlowEdgeComponent)

	def test_TensorFlowEdgeComponent_fails_without_valid_actionActuator(self):
		#Fails if actuator_udm not of function type
		with self.assertRaises(Exception):
			edge_component = TensorFlowEdgeComponent(ModelPath, "asd")
			assertNotIsInstance(edge_component, TensorFlowEdgeComponent)

	def test_TensorFlowEdgeComponent_takes_valid_actionActuator(self):
		edge_component = TensorFlowEdgeComponent(ModelPath, actuator_udm)
		assert isinstance(edge_component, TensorFlowEdgeComponent)

if __name__ == '__main__':
	unittest.main()
