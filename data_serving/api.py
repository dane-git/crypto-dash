import logging
import requests
from flask import Flask, jsonify, request
from db_utils import fetch_ticker_data, fetch_recent_trades, fetch_trades_since
from flask_cors import CORS
from datetime import datetime, timedelta
import pandas as pd
import warnings

app = Flask(__name__)
# Enable CORS for all routes and origins
CORS(app)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
# Configure logging
# logging.basicConfig(
#     filename='api_all.log',  # Log file name
#     level=logging.ERROR,        # Log level
#     format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
# )
# logger = logging.getLogger(__name__)



import re

def clean_timestamp(ts):
    if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", ts):  # ISO format
        return ts.replace("T", " ")
    elif re.match(r".*\sGMT", ts):  # Handle GMT suffix
        return ts[:-4].strip()
    return ts

# Function to log outbound HTTP requests
def log_request(url, method="GET", params=None, data=None, headers=None):
    try:
        # logger.info(f"Making {method} request to {url} with params={params}, data={data}, headers={headers}")
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            # logger.warning(f"Unsupported HTTP method: {method}")
            return None

        # logger.info(f"Response from {url}: {response.status_code} - {response.text}")
        return response
    except Exception as e:
        # logger.error(f"Error during outbound request to {url}: {e}", exc_info=True)
        return None


def bin_time_price_data(times, prices, bin_size="10s"):
    """
    Bin time and price data into specified intervals.
    
    Args:
        times (list[datetime]): List of datetime objects.
        prices (list[float]): List of corresponding prices.
        bin_size (str): Binning interval, e.g., "1min", "5min", "1H".
    
    Returns:
        tuple: Binned times and prices as lists.
         Code	        Meaning	            Example Binning Size
         L	            Millisecond	        "10L" (10 ms bins)
         s	            Second	            "15S" (15-second bins)
         T or min	    Minute	            "1T" or "1min" (1-minute bins)
         H	            Hour	            "2H" (2-hour bins)
         D	            Day	                "1D" (1-day bins)
         B	            Business Day (Mon-Fri)	"1B" (1 business day bins)
         W	            Week (Sunday as start of week)	"1W" (1-week bins)
         W-MON	Week (Monday as start of week)	"1W-MON" (1-week bins starting Monday)
         M	            Month (Month-end frequency)	"1M" (1-month bins)
         MS	            Month (Month-start frequency)	"1MS" (1-month bins starting from the first of the month)
         Q	            Quarter (3 months, quarter-end)	"1Q" (1-quarter bins)
         QS	            Quarter (Quarter-start frequency)	"1QS" (1-quarter bins starting the first month of the quarter)
         A or Y	Year (Year-end frequency)	"1A" or "1Y" (1-year bins)
         AS or YS	    Year (Year-start frequency)	"1AS" or "1YS" (1-year bins starting January 1st)
    """
    
    # Create a DataFrame
    data = pd.DataFrame({"time": times, "price": prices})
    
    # Ensure 'time' is a datetime object
    if not isinstance(data["time"].iloc[0], pd.Timestamp):
        data["time"] = data["time"].apply(clean_timestamp)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            data["time"] = pd.to_datetime(data["time"], errors="coerce")
    
    # Set 'time' as the DataFrame index
    data.set_index("time", inplace=True)
    
    # Perform binning using resample
    binned_data = data.resample(bin_size).mean().dropna()
    
    # Reset index to get 'time' as a column
    binned_data.reset_index(inplace=True)
    
    # Return binned times and prices as lists
    return binned_data["time"].tolist(), binned_data["price"].tolist()


@app.route('/api/ticker_data', methods=['GET'])
def get_ticker_data():
    """API endpoint to fetch ticker data."""
    product_id = request.args.get('product_id')
    start_time = request.args.get('start_time')  # ISO format expected
    end_time = request.args.get('end_time')  # Optional
    try:
        # Convert start_time to datetime and make it timezone-naive
        start_time = pd.to_datetime(start_time).tz_localize(None)
    except Exception as e:
        return jsonify({"error": f"Invalid start_time format: {str(e)}"}), 400

    # TODO PASS THIS IN
    bin_size = "10s"
    if not product_id or not start_time:
        return jsonify({"error": "Missing 'product_id' or 'start_time'"}), 400

    data = fetch_ticker_data(product_id, start_time, end_time)
    df = pd.DataFrame(data)
    df['_time'] = pd.to_datetime(df['time'])
    df = df[df['_time'] >= start_time]
    raw_data = df.to_dict(orient='records')
    times = [entry["time"] for entry in raw_data]
    prices = [entry["price"] for entry in raw_data]
    binned_times, binned_prices = bin_time_price_data(times, prices, bin_size)
    result = [{"time": t.isoformat(), "price": p} for t, p in zip(binned_times, binned_prices)]
    return jsonify(result)
    

@app.route('/api/recent_trades', methods=['GET'])
def get_recent_trades():
    """API endpoint to fetch recent trades."""
    product_id = request.args.get('product_id')
    limit = int(request.args.get('limit', 10))  # Default to 10 trades

    if not product_id:
        return jsonify({"error": "Missing 'product_id'"}), 400

    try:
        # Fetch recent trades
        data = fetch_recent_trades(product_id, limit)

        # Sort trades by time in descending order (most recent first)
        data = sorted(data, key=lambda x: x['time'], reverse=True)

        # Limit the results to the specified number
        data = data[:limit]

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/api/aggregated_trades', methods=['GET'])
def get_aggregated_trades():
    """
    API endpoint to fetch and aggregate trades since the last update.
    Aggregates buy/sell sizes and averages prices for a given product_id.
    """
    product_id = request.args.get('product_id')
    since_timestamp = request.args.get('since')  # ISO format expected

    if not product_id or not since_timestamp:
        return jsonify({"error": "Missing 'product_id' or 'since'"}), 400

    try:
        since_timestamp = pd.to_datetime(since_timestamp)  # Convert to datetime
    except Exception as e:
        return jsonify({"error": "Invalid 'since' format"}), 400

    # Fetch trades since the given timestamp
    trades = fetch_trades_since(product_id, since_timestamp)

    if not trades:
        return jsonify({
            "buys": {"total_size": 0, "avg_price": 0, "count": 0},
            "sells": {"total_size": 0, "avg_price": 0, "count": 0}
        })

    # Aggregate buys and sells
    buys = [trade for trade in trades if trade['side'] == 'BUY']
    sells = [trade for trade in trades if trade['side'] == 'SELL']

    def aggregate(trades):
        total_size = sum(float(trade['size']) for trade in trades)
        avg_price = (sum(float(trade['price']) * float(trade['size']) for trade in trades) / total_size) if total_size > 0 else 0
        return {"total_size": total_size, "avg_price": avg_price, "count": len(trades)}

    aggregated_data = {
        "buys": aggregate(buys),
        "sells": aggregate(sells),
    }

    return jsonify(aggregated_data)

@app.route('/api/last_trade', methods=['GET'])
def get_last_trade():
    """API endpoint to fetch the last trade for a given product."""
    product_id = request.args.get('product_id')

    if not product_id:
        return jsonify({"error": "Missing 'product_id'"}), 400

    data = fetch_recent_trades(product_id, limit=1)  # Fetch the most recent trade
    print(data)
    if not data:
        return jsonify({"error": "No trades found"}), 404

    return jsonify(data[0])  # Return the single most recent trade
if __name__ == '__main__':
    app.run(port=5000, debug=True)
