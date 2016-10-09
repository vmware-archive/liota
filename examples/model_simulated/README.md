Examples for Pint Enabled Simulated Models
---

Examples in this folder shows how developers can use pint to avoid
unit/dimension mistakes and mismatches while developing a liota app.

Files here include two simulated physical models:
- `bike_model_simulated.py`
- `thermistor_model_simulated.py`

An object of either classes will create a thread, that changes some states of 
the model randomly over time. There are getter methods that can be called from
the app to retrieve the states.

There are also example liota apps that reads these simulated models and create
metrics for either Graphite or vROps.

These two files are apps using Graphite DCC:

- `graphite_bike_model_simulated.py`
- `graphite_thermistor_model_simulated.py`

These two files are apps using vROps DCC:

- `vrops_bike_model_simulated.py`
- `vrops_thermistor_model_simulated.py`

In these applications, there are physical computation methods defined, taking
pint Quantity objects as arguments and returning Quantity objects, too. An 
app creates a simulated physical model object on startup. The sampling method
access the model states using methods provided by the models, conduct pint
enabled physical computations on them, and returns the result of computation.

Units in the same dimension will be convert automatically by pint.

In event of a dimension mismatch, that happens in either dimension check or 
unit conversion, pint throws an exception during runtime, so further
misuse of values in wrong units can be prevented.

In `graphite_thermistor_model_simulated.py` and
`vrops_thermistor_model_simulated.py`, we have provided a
**counter example**
(commented out) showing how a dimension mismatch can be caused. Using those
code pieces will result in runtime exceptions.
