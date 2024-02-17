# pgnotefi
pgnotefi is a Python library crafted to empower applications with real-time PostgreSQL event notifications for efficient cache invalidation, directly leveraging existing PostgreSQL infrastructure. This approach eliminates the need for additional technologies for cache management, simplifying your stack while enhancing performance and real-time data consistency.

## Key Advantages
- **Leverage Existing Infrastructure**: Utilizes PostgreSQL's native NOTIFY/LISTEN capabilities for event-driven cache invalidation, avoiding the overhead of integrating external caching systems.
- **Asynchronous and Efficient**: Built on top of `asyncpg` for asynchronous database communication, ensuring non-blocking I/O operations and optimal performance.
- **Flexible Cache Invalidation Strategies**: Offers a variety of strategies (e.g., Greedy, Windowed, Timed) for nuanced cache invalidation control, tailored to different application needs.
- **Simple Yet Powerful API**: Designed with simplicity in mind, offering a straightforward setup process and an intuitive API for managing cache invalidation logic.

## Installation
To install pgnotefi, run the following command in your terminal:
```bash
pip install pgnotefi
```

## Using pgnotefi
### Setting Up
Initialize PostgreSQL triggers to emit NOTIFY events on data changes. pgnotefi provides utility scripts for easy trigger setup
```bash
pgnotefi install --tables your_table_names
```

### FastAPI Example
Example showing how to use pgnotefi for cache invalidation in a FastAPI app

```python
from fastapi import FastAPI
from pgnotefi import decorators, listeners, models, strategies

app = FastAPI()

async def setup_app(channel: models.PGChannel) -> FastAPI:
    listener = await listeners.PGEventQueue.create(channel)

    @decorators.cache(strategy=strategies.Greedy(listener=listener))
    async def cached_query():
        # Simulate a database query
        return {"data": "query result"}

    @app.get("/data")
    async def get_data():
        return await cached_query()

    return app
```