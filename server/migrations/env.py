import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context
import os
from app.db.base import Base
from app.core.config import settings
from app.models import user, group, student, grade, course, assignment, submission, gradebook, feedback, schedule

target_metadata = Base.metadata

# Ensure UTF-8 client encoding for psycopg2
os.environ.setdefault("PGCLIENTENCODING", "UTF8")

# Prefer explicit env, then application settings (local defaults)
DB_URL = (
    os.getenv("DB_URL_SYNC")
    or os.getenv("DB_URL")
    or os.getenv("DATABASE_URL")
    or settings.get_db_url(for_migration=True)
)
config = context.config
config.set_main_option("sqlalchemy.url", DB_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

from sqlalchemy import create_engine

def run_migrations_online() -> None:
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    with open("db_url_debug.txt", "w", encoding="utf-8") as f:
        f.write(f"DB_URL: {repr(DB_URL)}\n")
        f.write(f"config.get_main_option('sqlalchemy.url'): {repr(config.get_main_option('sqlalchemy.url'))}\n")
    with connectable.connect() as connection:
        do_run_migrations(connection)
    connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()