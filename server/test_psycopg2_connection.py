import os
import psycopg2


def env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value if value is not None else default


def connect_from_env():
    dsn = env("DB_URL_SYNC") or env("DATABASE_URL_SYNC")
    if dsn:
        # Убираем SQLAlchemy префикс для чистого psycopg2 DSN
        if dsn.startswith("postgresql+psycopg2://"):
            dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
        elif dsn.startswith("postgresql+asyncpg://"):
            dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")
        return psycopg2.connect(dsn)

    # fallback to discrete params
    return psycopg2.connect(
        dbname=env("POSTGRES_DB", "eduanalytics"),
        user=env("POSTGRES_USER", "edua"),
        password=env("POSTGRES_PASSWORD", "secret"),
        host=env("POSTGRES_HOST", "localhost"),
        port=int(env("POSTGRES_PORT", "5432")),
    )


if __name__ == "__main__":
    try:
        os.environ.setdefault("PGCLIENTENCODING", "UTF8")
        with connect_from_env() as conn:
            with conn.cursor() as cur:
                cur.execute("select version();")
                print("Connection successful!", cur.fetchone()[0])
    except Exception as e:
        print(f"Connection failed: {e}")