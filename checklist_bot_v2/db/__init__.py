import asyncpg
from .models import CREATE_TABLES

pool: asyncpg.Pool = None

async def init_db(dsn: str):
    global pool
    pool = await asyncpg.create_pool(dsn)
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLES)
    return pool
