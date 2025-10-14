#!/bin/sh
set -e

# Configure logging timestamp
log_msg() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log_msg "Starting Door Service..."
log_msg "Current DATABASE_URL: ${DATABASE_URL}"  # Debug line
log_msg "Waiting for database to be ready..."

python << END
import sys
import time
import psycopg2
import os

# Get database parameters from environment
db_user = os.getenv('POSTGRES_USER')
db_pass = os.getenv('POSTGRES_PASSWORD')
db_name = os.getenv('POSTGRES_DB')
db_host = os.getenv('POSTGRES_HOST', 'db')  # This is the service name in docker-compose
db_port = os.getenv('POSTGRES_PORT', '5432')

print(f"Attempting to connect to database at {db_host}:{db_port}")

while True:
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        conn.close()
        break
    except psycopg2.OperationalError as e:
        sys.stdout.write(f"Database not ready yet. Error: {str(e)}\n")
        sys.stdout.flush()
        time.sleep(1)
END

log_msg "Database is ready. Running migrations..."
PYTHONPATH=/app alembic upgrade head || {
    log_msg "ERROR: Database migration failed"
    exit 1
}

log_msg "Database migrations completed successfully"
log_msg "Starting Streamlit application..."
streamlit run service/app.py --server.address=0.0.0.0