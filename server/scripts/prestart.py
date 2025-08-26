import os
import time
import subprocess
import sys


def run_cmd(cmd: list[str]) -> int:
    try:
        print(f"[prestart] Running: {' '.join(cmd)}")
        return subprocess.call(cmd)
    except Exception as e:
        print(f"[prestart] Error running {' '.join(cmd)}: {e}")
        return 1


def check_db_encoding() -> None:
    import psycopg2
    from urllib.parse import urlparse

    dsn = os.getenv("DB_URL_SYNC") or os.getenv("DATABASE_URL")
    if not dsn:
        print("[prestart] No DB_URL_SYNC/DATABASE_URL provided, skipping encoding check")
        return

    # Убираем SQLAlchemy префикс для чистого psycopg2 DSN
    if dsn.startswith("postgresql+psycopg2://"):
        dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
    elif dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")

    os.environ.setdefault("PGCLIENTENCODING", "UTF8")
    try:
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW server_encoding;")
                server_enc = cur.fetchone()[0]
                cur.execute("SHOW client_encoding;")
                client_enc = cur.fetchone()[0]
        print(f"[prestart] server_encoding={server_enc}, client_encoding={client_enc}")
    except Exception as e:
        print(f"[prestart] Encoding check failed: {e}")


def alembic_upgrade_with_retries(max_retries: int = 8, delay_seconds: int = 3) -> None:
    for attempt in range(1, max_retries + 1):
        code = run_cmd([sys.executable, "-m", "alembic", "upgrade", "head"])
        if code == 0:
            print("[prestart] Alembic upgrade successful")
            return
        print(f"[prestart] Alembic upgrade failed (attempt {attempt}/{max_retries}). Retrying in {delay_seconds}s...")
        time.sleep(delay_seconds)
    raise SystemExit("[prestart] Alembic upgrade failed after retries")


if __name__ == "__main__":
    os.environ.setdefault("PGCLIENTENCODING", "UTF8")
    check_db_encoding()
    alembic_upgrade_with_retries()



