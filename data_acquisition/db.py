import asyncio
from asyncpg import create_pool
from dotenv import load_dotenv
import os

# Load environment variables from ./private/private.env
load_dotenv(dotenv_path="../private/private.env")

DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DB"),
    "host": "localhost",  # Change to "postgres" if running within Docker Compose
    "port": 5432
}

# Global connection pool
db_pool = None

async def init_db_pool():
    """Initialize the asyncpg connection pool."""
    global db_pool
    if db_pool is None:
        db_pool = await create_pool(**DB_CONFIG)
        print("Database pool initialized.")
        print("THERE IS A db_pool")

async def close_db_pool():
    """Close the asyncpg connection pool."""
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None
        print("Database pool closed.")

CREATE_TABLES_QUERY = """
CREATE TABLE IF NOT EXISTS ticker_data (
    id SERIAL PRIMARY KEY,
    product_id TEXT NOT NULL,
    time TIMESTAMP NOT NULL,
    price NUMERIC NOT NULL
);

CREATE TABLE IF NOT EXISTS trade_data (
    id SERIAL PRIMARY KEY,
    product_id TEXT NOT NULL,
    time TIMESTAMP NOT NULL,
    trade_id TEXT NOT NULL,
    price NUMERIC NOT NULL,
    size NUMERIC NOT NULL,
    side TEXT NOT NULL
);

-- Indexes for efficient filtering
CREATE INDEX IF NOT EXISTS idx_product_id_time_ticker ON ticker_data (product_id, time);
CREATE INDEX IF NOT EXISTS idx_product_id_time_trade ON trade_data (product_id, time);
CREATE INDEX IF NOT EXISTS idx_time_ticker ON ticker_data (time);
CREATE INDEX IF NOT EXISTS idx_time_trade ON trade_data (time);
"""

CREATE_MATERIALIZED_VIEWS_QUERY = """
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_ticker_summary AS
SELECT
    product_id,
    date_trunc('day', time) AS day_bin,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price
FROM ticker_data
GROUP BY product_id, day_bin;

-- Add a unique index for the materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_ticker_summary ON daily_ticker_summary (product_id, day_bin);

CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_ticker_summary AS
SELECT
    product_id,
    date_trunc('hour', time) AS hour_bin,
    AVG(price) AS avg_price,
    MIN(price) AS min_price,
    MAX(price) AS max_price
FROM ticker_data
GROUP BY product_id, hour_bin;

-- Add a unique index for the materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_hourly_ticker_summary ON hourly_ticker_summary (product_id, hour_bin);
"""

async def initialize_db():
    """Initialize database with necessary tables and views."""
    if db_pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_db_pool() first.")
    async with db_pool.acquire() as conn:
        await conn.execute(CREATE_TABLES_QUERY)
        await conn.execute(CREATE_MATERIALIZED_VIEWS_QUERY)
    print("Database initialized.")

async def periodic_refresh():
    """Refresh materialized views periodically."""
    if db_pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_db_pool() first.")
    while True:
        async with db_pool.acquire() as conn:
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY daily_ticker_summary;")
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_ticker_summary;")
        print("Materialized views refreshed.")
        await asyncio.sleep(3600)  # Refresh every hour

async def insert_ticker(product_id, time, price):
    """Insert ticker data into the database."""
    if db_pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_db_pool() first.")
    query = """
    INSERT INTO ticker_data (product_id, time, price)
    VALUES ($1, $2, $3)
    """
    async with db_pool.acquire() as conn:
        await conn.execute(query, product_id, time, price)

async def insert_trade(product_id, time, trade_id, price, size, side):
    """Insert trade data into the database."""
    if db_pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_db_pool() first.")
    query = """
    INSERT INTO trade_data (product_id, time, trade_id, price, size, side)
    VALUES ($1, $2, $3, $4, $5, $6)
    """
    async with db_pool.acquire() as conn:
        await conn.execute(query, product_id, time, trade_id, price, size, side)

# async def fetch_ticker_data(product_id, start_time=None):
#     """Fetch ticker data asynchronously."""
#     if db_pool is None:
#         raise RuntimeError("Database pool is not initialized.")
#     query = """
#     SELECT time, price FROM ticker_data
#     WHERE product_id = $1 AND time >= $2
#     ORDER BY time DESC
#     """
#     async with db_pool.acquire() as conn:
#         rows = await conn.fetch(query, product_id, start_time)
#     return [{"time": row["time"], "price": row["price"]} for row in rows]

# async def fetch_recent_trades(product_id, limit=10):
#     """Fetch recent trade data asynchronously."""
#     if db_pool is None:
#         raise RuntimeError("Database pool is not initialized.")
#     query = """
#     SELECT trade_id, price, size, side, time FROM trade_data
#     WHERE product_id = $1
#     ORDER BY time DESC
#     LIMIT $2
#     """
#     async with db_pool.acquire() as conn:
#         rows = await conn.fetch(query, product_id, limit)
#     return [{"trade_id": row["trade_id"], "price": row["price"], "size": row["size"], "side": row["side"], "time": row["time"]} for row in rows]


# def fetch_ticker_data_sync(product_id, start_time=None):
#     """Synchronous wrapper for fetching ticker data."""
#     return asyncio.run(fetch_ticker_data(product_id, start_time))

# def fetch_recent_trades_sync(product_id, limit=10):
#     """Synchronous wrapper for fetching recent trades."""
#     return asyncio.run(fetch_recent_trades(product_id, limit))
