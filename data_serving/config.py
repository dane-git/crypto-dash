from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(dotenv_path="../private/private.env")

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": "localhost",  # Adjust for Docker as needed
    "port": 5432,
}
