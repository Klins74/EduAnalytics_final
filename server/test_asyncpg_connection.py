import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(user='edua', password='secret', database='eduanalytics', host='localhost', port=5432)
        print('Connected successfully')
        await conn.close()
    except Exception as e:
        print('Connection failed:', e)

if __name__ == "__main__":
    asyncio.run(test())