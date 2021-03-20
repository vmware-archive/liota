# Influx
InfluxDB is a time series database built from the ground up to handle high write and query loads. It is the second piece of the TICK stack. InfluxDB is meant to be used as a backing store for any use case involving large amounts of timestamped data, including DevOps monitoring, application metrics, IoT sensor data, and real-time analytics.
# Requirements
  - Mqtt Broker: Setup a mqtt broker which will allow liota to send metrics to the collector agent.
 
  - Telegraf: Telegraf is a plugin-driven server agent for collecting & reporting metrics. You can setup telegraf from [here.](https://docs.influxdata.com/telegraf/v1.4/)
  
- InfluxDB: You can install and configure InfluxDb from [here.](https://docs.influxdata.com/influxdb/v1.3/introduction/)

# Examples
Above examples are sending metrics data to the mqtt broker, from where you can consume data using telegraf agent which will then pass data to InfluxDB. 

You can also view data being sent to InfluxDB using Chronograf. You can setup chronograf from [here.](https://docs.influxdata.com/chronograf/v1.3/)

