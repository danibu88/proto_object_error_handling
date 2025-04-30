# test_env.py
from dotenv import load_dotenv
import os

load_dotenv()

print("Database Environment Variables:")
print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB')}")
print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER')}")
print(f"POSTGRES_PASSWORD: {'[SET]' if os.getenv('POSTGRES_PASSWORD') else '[NOT SET]'}")

# Construct and print the database URL
db_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@localhost:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
print(f"\nConstructed Database URL: {db_url}")