# Coinbase market data feeds insights

## 1. PoC Tool

- highest bid -> best bid 
- lowest ask -> best ask

### Assumptions
- Don't overcomplicate it (important).
- The application runs in the foreground in the terminal.
- The user needs to specify a valid `product_id` when starting the application.
- We're only interested in metrics for data collected *after* the application has started. 
- The output only needs to be printed in the terminal, and not saved to a persistent datastore.
- Forecasted mid-price in 60 seconds is a direct multi-step forecasting cased on previous values.
  - In this case, it will be step T+12, if there's a 5 second interval between messages.

### References
- https://github.com/python-websockets/websockets
- https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-channels
- https://stackoverflow.com/questions/66683387/coinbase-websocket-channel-match-vs-ticker
- https://www.coinbase.com/learn/advanced-trading/what-is-an-order-book
- https://skforecast.org/0.10.0/index.html#
- https://joaquinamatrodrigo.github.io/skforecast/0.10.0/introduction-forecasting/introduction-forecasting.html#direct-multi-step-forecasting


## 2. Public Cloud Architecture

Based on a subset of the architecture as described in the Analytics end-to-end with Azure Synapse architecture, which covers ingestion, storage, processing and enriching and finally serving the data to end-users to provide insights. The architecture here is similar to the *cold* path, as the real-time data doesn't need do be served live to the end users.


![Public Cloud Architecture in Azure](./docs/public_cloud_architecture.svg)


This particular "standard" architecure was chosen for a couple of reasons:
- Don't reinvent the wheel. Even though equivalent results can be achieved using similar services, or platforms, starting from a setup which can be later be changed based on requirements or needs is favourable.
- Familiar architecure. I've previously worked with Azure Synapse Analytics and Azure Machine Learning to process data and perform predictions, in addition to deploying applications to Azure App Service.

#### Ingest
##### Azure App Service
Deploy a containerized application to initiate a websocket connection with the Coinbase WebSocket feeds. Note that the application needs to be running as a service in order to continuously ingest the updates from the feeds, and can act as a producer client to send the received JSON payloads to Event Hub.

##### Azure Event Hub
Ingest the feeds data sent in the previous step. The event data can then be stored, either as parquet or JSON, preserving the sequence order. Also allows additional consumers to further ingest or process the data, for example in Azure Stream Analytics for a *hot* path.

#### Store
##### Azure Data Lake Storage
Persist the raw marked data feed responses in a Raw data lake layer.

#### Process and enrich
##### Azure Synapse Analytics
Batch processing of the feed data using Spark notebooks to transform the data. Synapse Analytics contains various services, such as additional storage accounts or SQL pools, to store data in various layers. Mid-prices prices can be calculated per record and averages aggregated over given time periods. 

Synapse Analytics is also tightly coupled with Azure Machine Learning, allowing forecasts to be predicted and later compared with the actual mid-price once it arrives in the pipeline, and calculate the forecasting errors and averages aggregated.

##### Azure Machine Learning
Train and invoke ML models to predict future mid-price forecasts. Existing models can be deployed, or new ones trained on existing forecast data available in one of the data layers.

#### Serve:
##### Power BI
Datasets can be directly loaded from the final data layer to create visualization for the end-users.

##### Data warehouse
The final data layer can also be copied into a data warehouse for storage and further analysis of the data for more advanced end users. 


### References
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/dataplate2e/data-platform-end-to-end?tabs=portal
- https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-about