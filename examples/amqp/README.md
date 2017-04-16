# Using AMQP as Transport in LIOTA

LIOTA offers AMQP protocol as transport to communicate with DCC via [AmqpDccComms](https://github.com/vmware/liota/blob/master/liota/dcc_comms/amqp_dcc_comms.py).

## Protocol Version

Currently, LIOTA supports AMQP version **0.9.1**

## Connection and Channels

LIOTA uses separate AMQP connections for publisher and consumer.  This helps to avoid blocking of consumers during broker overload, as AMQP brokers
(Ex: RabbitMQ) block publishing connections in case of broker overload.

Each AMQP connection has its own channel in LIOTA.  So, one channel for publisher and one for consumer.

## Exchanges

**direct, topic, fanout and headers** exchange types are supported.


## Using AmqpDccComms

AmqpDccComms provides the flexibility of operating in three different modes for publishing. **AmqpPublishMessagingAttributes class** in [amqp.py](https://github.com/vmware/liota/blob/master/liota/lib/transports/amqp.py)
provides this flexibility.

### AmqpPublishMessagingAttributes

#### Default Values:

* edge_system_name, exchange_name, routing_key, header_args will **None**
* exchange_type will be **topic**
* exchange_durable will be **False**
* msg_delivery_mode will be **1** which is **Transient**


**Mode 1:** Single exchange and routing-key (auto-generated or from configuration file) for all metrics published from an edge_system over a single AMQP publisher connection.  Default values in this case are:
* Publish exchange_name for all Metrics will be **liota.exchange.generated_local_uuid_of_edge_system**
* routing_key for all Metrics will be **liota.generated_local_uuid_of_edge_system.request**

**-** In this mode, AMQP message's payload MUST be self-descriptive so that, consumer can consume and process by parsing payload. i.e., Along with stats of metric, its edge_system's_name, device's_name will also be appended with the payload.

**Mode 2:** Single exchange and different routing-keys for each metric published from an edge_system.

**Mode 3:** Separate exchange and routing-keys for each metric published from an edge_system.

**-** In Mode 2 & 3, AMQP message's payload need not be self-descriptive.  Consumers can consume the messages from exchanges based on routing-key.

**NOTE:** AmqpPublishMessagingAttributes for a RegisteredMetric object MUST always be passed via **msg_attr** attribute of that RegisteredMetric Object.


Similarly, **AmqpConsumeMessagingAttributes class** in [amqp.py](https://github.com/vmware/liota/blob/master/liota/lib/transports/amqp.py) facilitates binding queues with exchanges, and consume messages from those queues.

### AmqpConsumeMessagingAttributes

#### Default Values:

* edge_system_name, exchange_name, queue_name, routing_keys, callback, header_args will be **None**
* exchange_type will be **topic**
* exchange_durable, queue_durable, queue_exclusive, queue_no_ack will be **False**
* queue_auto_delete will be **True**
* prefetch_size, prefetch_count will be **Zero**

LIOTA also supports auto-generation of AmqpConsumeMessagingAttributes by simply providing a **auto_gen_callback** in AmqpDccComms.   Default values in this case are:
* Publish exchange_name will be **liota.exchange.generated_local_uuid_of_edge_system**
* routing_key will be **liota.generated_local_uuid_of_edge_system.response**
* queue_name will be **liota.queue.generated_local_uuid_of_edge_system**

A single AMQP Transports instance allows **only one** active publisher and consumer connection.  **consume()** can be called only once and will throw error if called without cancelling existing consumer.
So, **AmqpConsumeMessagingAttributes must be passed as list** and AMQP transports will create a **AmqpConsumerWorker** which in turn creates corresponding number of consumers for each AmqpConsumeMessagingAttributes in the list.

**NOTE:** callback methods should not be blocking as AmqpConsumerWorker might be blocked and affect other Consumers.  Any blocking job should be offloaded to a separate thread.


**Examples:**

[RabbitMQ DCC](https://github.com/vmware/liota/blob/master/liota/dccs/rabbitmq.py) is used to showcase publishing and consuming using Amqp transports and DccComms.

* [auto_gen](https://github.com/vmware/liota/blob/master/examples/amqp/rabbitmq/simulated_home_auto_gen.py) publishes to RabbitMQ using **Mode 1** and consume from auto-generated exchange using auto-generated routing key and queue.
* [single_exchange_and_routing_key_per_metric](https://github.com/vmware/liota/blob/master/examples/amqp/rabbitmq/simulated_home_single_exchange_routing_key_per_metric.py) publishes to RabbitMQ using **Mode 2** and consumes from single exchange using different routing keys and queues.
* [exchange_and_routing_key_per_metric](https://github.com/vmware/liota/blob/master/examples/amqp/rabbitmq/simulated_home_exchange_and_routing_key_per_metric.py) publishes to RabbitMQ using **Mode 3** and consumes from multiple exchanges using different queues.

Refer respective class's docstring for more information on parameters.

**NOTE:**
If **Mode 1** is used, `generated_local_uuid_of_edge_system` will be written to a file available at path **uuid_path** as specified in [liota.conf](https://github.com/vmware/liota/blob/master/config/liota.conf) file.  Users can refer this file to get the uuid.
