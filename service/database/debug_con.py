import os
from dotenv import load_dotenv
import psycopg2
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Print environment variables
logger.debug(f"POSTGRES_USER: {os.getenv('POSTGRES_USER')}")
logger.debug(f"POSTGRES_DB: {os.getenv('POSTGRES_DB')}")
logger.debug(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

# Try connection
try:
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
    )
    logger.debug("Connection successful!")
except Exception as e:
    logger.error(f"Connection failed: {str(e)}")
