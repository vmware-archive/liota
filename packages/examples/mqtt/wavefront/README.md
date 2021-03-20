# Wavefront
[![N|Solid](https://docs.wavefront.com/images/wavefront_architecture_lb.png)](https://docs.wavefront.com/images/wavefront_architecture_lb.png)

Wavefront is a high performance streaming analytics platform designed for monitoring and optimization. The service is unique in its ability to scale to very high data ingestion rates and query loads.
# Requirements
  - Mqtt Broker: Setup a mqtt broker which will allow liota to send metrics to the collector agent.
  
  - Collector Agent: Collector agents collect metrics from monitored systems and send them to the Wavefront proxy. Monitored systems can include hosts, containers, and many different types of applications. Wavefront supports many standard collector agents, including Telegraf, Docker cAdvisor, and others. You can check the integration of collector agent [here.](https://docs.wavefront.com/integrations.html)
  
- Wavefront Proxy: The Wavefront proxy allows you to send your data to Wavefront in a secure, fast, and reliable manner. The proxy works with the Wavefront server to ensure end-to-end flow control. 

# Examples
Above examples are sending metrics data to the mqtt broker, from where you can consume data using any collector agent which will then pass data to wavefront proxy to be displayed in wavefront.

You can learn how to get data into wavefront [here.](https://docs.wavefront.com/tutorial_data_ingestion.html)

