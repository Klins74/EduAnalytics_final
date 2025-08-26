import asyncio
import asyncpg
import os


def env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value if value is not None else default


async def test():
    try:
        os.environ.setdefault("PGCLIENTENCODING", "UTF8")
        
        dsn = env("DB_URL") or env("DATABASE_URL")
        if dsn and dsn.startswith("postgresql+asyncpg://"):
            dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")
        
        if dsn:
            conn = await asyncpg.connect(dsn)
        else:
            conn = await asyncpg.connect(
                user=env("POSTGRES_USER", "edua"),
                password=env("POSTGRES_PASSWORD", "secret"),
                database=env("POSTGRES_DB", "eduanalytics"),
                host=env("POSTGRES_HOST", "db"),
                port=int(env("POSTGRES_PORT", "5432"))
            )
        
        version = await conn.fetchval("SELECT version();")
        print('Connected successfully!', version)
        await conn.close()
    except Exception as e:
        print('Connection failed:', e)


if __name__ == "__main__":
    asyncio.run(test())