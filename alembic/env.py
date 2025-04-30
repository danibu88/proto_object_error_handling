import os
import sys
import logging
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Load environment variables from .env file
load_dotenv()

# this is the Alembic Config object
config = context.config

# Import the MetaData object from your models
from tsb_door_service.database.models import Base

target_metadata = Base.metadata

# Construct the database URL from environment variables
db_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST', 'db')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"

# Override sqlalchemy.url in alembic.ini with constructed URL
config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("alembic")
logger.info(f"Database URL in env.py: {db_url}")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # Log migration start
    logger.info("Starting database migrations...")
    start_time = datetime.now(pytz.timezone("Europe/Berlin"))

    try:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,  # Add type comparison
            )

            with context.begin_transaction():
                context.run_migrations()

        # Log successful completion and duration
        duration = datetime.now(pytz.timezone("Europe/Berlin")) - start_time
        logger.info(
            f"Database migrations completed successfully in {duration.total_seconds():.2f} seconds"
        )

    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
