import asyncpg
import asyncio

async def test():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/eduanalytics')
        print('Connection successful')
        await conn.close()
    except Exception as e:
        print('Connection failed:', e)

if __name__ == "__main__":
    asyncio.run(test())