import asyncio
from db import init_db_pool, close_db_pool, insert_ticker, insert_trade, initialize_db
from coinbase.websocket import WSClient
from datetime import datetime
import json

# Load API keys
with open('../private/cdp_api_key.json') as jsf:
    key_data = json.load(jsf)
api_key = key_data['name']
api_secret = key_data['privateKey']

SUBS = ["BTC-USD", "ETH-USD", "ADA-USD", "MUSE-USD"]

async def initialize_resources():
    """Initialize the database pool and prepare the database."""
    await init_db_pool()
    await initialize_db()

async def process_message(msg):
    """Process WebSocket messages and save them to the database."""
    if msg is None:
        return
    try:
        if isinstance(msg, str):
            msg = json.loads(msg)

        channel = msg.get("channel")
        if channel == "ticker":
            for event in msg.get("events", []):
                for ticker in event.get("tickers", []):
                    await insert_ticker(
                        ticker["product_id"],
                        datetime.fromisoformat(msg["timestamp"].replace("Z", "")),
                        float(ticker["price"])
                    )
        elif channel == "market_trades":
            for event in msg.get("events", []):
                for trade in event.get("trades", []):
                    await insert_trade(
                        trade["product_id"],
                        datetime.fromisoformat(trade["time"].replace("Z", "")),
                        trade["trade_id"],
                        float(trade["price"]),
                        float(trade["size"]),
                        trade["side"]
                    )
    except Exception as e:
        print(f"Error processing message: {e}")

async def start_websocket():
    """Start the WebSocket client."""
    async def on_message(msg):
        await process_message(msg)

    loop = asyncio.get_running_loop()
    client = WSClient(
        api_key=api_key,
        api_secret=api_secret,
        on_message=lambda msg: asyncio.run_coroutine_threadsafe(on_message(msg), loop).result(),
    )
    client.open()
    client.subscribe(product_ids=SUBS, channels=["ticker", "market_trades", "heartbeats"])
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("WebSocket loop was cancelled.")
    finally:
        client.close()

async def run_all():
    """Run database initialization and WebSocket."""
    await initialize_resources()
    print('Resources initialized. Starting WebSocket...')
    await start_websocket()

def main():
    """Entry point to start the event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_all())
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        loop.run_until_complete(close_db_pool())
        loop.close()

if __name__ == "__main__":
    main()
