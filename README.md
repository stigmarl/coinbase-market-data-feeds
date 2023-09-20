
- highest bid -> best bid 
- lowest ask -> best ask

## Assumptions
- Don't overcomplicate it (important).
- The application runs in the foreground in the terminal.
- The user needs to specify a valid `product_id` when starting the application.
- We're only interested in metrics for data collected *after* the application has started. 
- The output only needs to be printed in the terminal, and not saved to a persistent datastore.

## References
- https://github.com/python-websockets/websockets
- https://docs.cloud.coinbase.com/advanced-trade-api/docs/ws-channels
- https://stackoverflow.com/questions/66683387/coinbase-websocket-channel-match-vs-ticker
- https://www.coinbase.com/learn/advanced-trading/what-is-an-order-book