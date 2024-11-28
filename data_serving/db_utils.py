import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG


def connect_to_db():
    """Create a new database connection."""
    return psycopg2.connect(**DB_CONFIG)


def fetch_ticker_data(product_id, start_time, end_time=None):
    """Fetch ticker data from the database."""
    query = """
    SELECT time, price 
    FROM ticker_data 
    WHERE product_id = %s AND time >= %s
    """
    params = [product_id, start_time]

    if end_time:
        query += " AND time <= %s"
        params.append(end_time)

    query += " ORDER BY time ASC"

    with connect_to_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def fetch_recent_trades(product_id, limit=10, msg=None):
    """Fetch recent trades from the database."""
    query = """
    SELECT trade_id, price, size, side, time 
    FROM trade_data 
    WHERE product_id = %s
    ORDER BY time DESC
    LIMIT %s
    """
    params = [product_id, limit]
    if msg is not None:
        print(msg)

    with connect_to_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
        
def fetch_trades_since(product_id, since_timestamp):
    query = """
        SELECT trade_id, price, size, side, time
        FROM trade_data
        WHERE product_id = %s AND time > %s
        ORDER BY time ASC
    """
    params = (product_id, since_timestamp)

    try:
        conn = connect_to_db()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            trades = cursor.fetchall()
            return trades
    except Exception as e:
        print(f"Database query failed: {e}")
        return []
    finally:
        conn.close()
