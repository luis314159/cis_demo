from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from db.connection import engine

@asynccontextmanager
async def get_session():
    async_session = AsyncSession(engine)
    try:
        yield async_session
    finally:
        await async_session.close()