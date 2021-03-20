# Edge Intelligence Models

This folder contains [PFA](http://dmg.org/pfa/docs/motivation/), [scikit-learn](http://scikit-learn.org/) and [TensorFlow](https://www.tensorflow.org/) and RuleEdgeComponent examples.
Trained PFA, scikit-learn and TensorFlow models are present under the trained_models directory.
The generated data is using the [TI SensorTag](http://www.ti.com/ww/en/wireless_connectivity/sensortag/) which has been used for training the windmill model.
It provides a basic example which uses TI SensorTag data to simulate a sample windmill model. The basic metrics we collect from Windmill model using TI SensorTag are: 
  - RPM 
  - Vibration
  - Ambient Temperature 
  - Relative Humidity.

The files ```windmill_tf_train.csv``` and ```windmill_tf_test.csv``` in trained_models directory are used for training and testing of accuracy of the TensorFlow model respectively. 
The file ```windmill_tf_model.py``` in trained_models directory is imdependent of Liota and used for creating the trained TensorFlow model and testing it's accuracy and prediction. 

# RuleEdgeComponent

Rule edge component is one of the edge intelligence components provided by Liota, you can define a simple rule depending on your requirement as a [python lambda](https://www.python-course.eu/lambda.php) function and the rule edge component will process the incoming metrics and the result can be passed onto actuator on basis of the rule you have defined as lambda function.

Currently tested for one metric only.

# Example
If you have to take rpm as a metric and if rpm exceeds certain limits you have to perform some action, you can define a lambda function as:
```
Rule = lambda rpm : 1 if (rpm>=rpm_limit) else 0
```
Now just create the ruleEdge and pass it onto RuleEdgeComponent along with the actuator_udm and exceed_limit.
actuator_udm can be used to pass on the value to the actuator, as of now we are printing them, here udm stands for user defined method.
exceed_limit is a parameter which can be specified about after how many times the limit is exceeded then action should be taken.
Example: If rpm exceeds rpm_limit consecutively exceed 3 times then only action should be applied, in that case we would assign exceed_limit = 3
```
edge_component = RuleEdgeComponent(ModelRule,exceed_limit,actuator_udm=action_actuator)
```
After this register the edge_component and start_collecting the values from sensor.
The values which will get published to RuleEdge component. Please refer the example file windmill_graphite_rule.py.
