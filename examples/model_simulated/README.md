Examples for Pint Enabled Simulated Models
---

Examples in this folder shows how developers can use pint to avoid
unit/dimension mistakes and mismatches while developing a liota app.

Liota provides two simulated physical model class:
- BikeSimulated
- ThermistorSimulated

An object of either classes will create a thread, that changes some states of 
the model randomly over time. There are getter methods that can be called
 to retrieve the states.

There are also example liota apps that reads from these simulated models and create
metrics for either Graphite or IOTCC.

These two files are apps using Graphite DCC:

- `graphite_bike_simulated.py`
- `graphite_thermistor_simulated.py`

These two files are apps using IOTCC DCC:

- `iotcc_bike_simulated.py`
- `iotcc_thermistor_simulated.py`

In these applications, there are physical computation methods defined, taking
pint Quantity objects as arguments and returning Quantity objects, too.
The sampling method access the model states using methods provided by the models,
conduct pint enabled physical computations on them, and returns the result
of computation.

Units in the same dimension will be convert automatically by pint.

In event of a dimension mismatch, that happens in either dimension check or 
unit conversion, pint throws an exception during runtime, so further
misuse of values in wrong units can be prevented.

In `graphite_thermistor_simulated.py` and
`iotcc_thermistor_simulated.py`, we have provided a
**counter example**
(commented out) showing how a dimension mismatch can be caused. Using those
code pieces will result in runtime exceptions.
