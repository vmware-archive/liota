# Offline data storage
If the client faces network disconnectivity, publish message can be stored as a persistent storage or in a temporary offline queue in which publish data will be added to an internal queue until the number of queued-up requests reaches the size limit of the queue. If the size of the queue is defined as negative integer it will act as a infinite queue. One can also choose the queue behaviour after it reaches it's specified size. If drop_oldest behaviour is set to be true, oldest publish message is dropped else the newest publish messages are dropped. One should specify the draining frequency in each case, which implies how data which has been stored will be published once the network connectivity is established. 
You can also specify data_drain_size which speicifes ow much data will be drained at once after the internet connectivity is established again. By default both are set to 1.

# Example
By default buffering_params is set to None, i.e buffering mechanism is disabled.
Suppose we want to create a persistent storage, while creating instance of DCC, we would pass the an instance of Buffering class along with it. 

```
buffering = Buffering(persistent_storage=True, data_drain_size=10, draining_frequency=1)
graphite = Graphite(SocketDccComms(ip=config['GraphiteIP'],port=8080), 
                offline_buffering=buffering)
```
Here data_drain_size is 1 and draining_frequency is 1 which specifies 10 messages will be sent per second.
For persistent storage a database will be created by the name of storage.db which will store all the messages while network connectivity is broken. 
Once network connectivity is back messages will be removed from database as they get published.
In case of ```persistent_storage``` as ```False``` the queueing mechanism will be used by default, you can specify queue_size and other parameters like drop_oldest, data_drain_size and draining_frequency: 
```
buffering = Buffering(queue_size=-1,data_drain_size=10, draining_frequency=1)
```
will create a queueing mechanism with infinite size and drop_behaviour by default is true, data_drain_size and draining_frequency can be any positive integer.
For queue with size 3 and drop_oldest behaviour set to true, 
```
buffering = Buffering(queue_size=3, drop_oldest=True, draining_frequency=1)
```
As the publish message arrives the queue will be like this after 3 publish message arrive:
```
['msg1', 'msg2', 'msg3']
```
As the fourth publish message arrives:
```
['msg2', 'msg3', 'msg4']
```
For the fifth publish message:
```
['msg3', 'msg4', 'msg5']
```
Similarly, if the drop_oldest behaviour is set to False:
```
['msg1', 'msg2', 'msg3']
```
After this any new coming publish message will be dropped.
