from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.client import Client

async def get_all_clients(session: AsyncSession):
    result = await session.execute(select(Client))
    return result.scalars().all()

async def add_client(session: AsyncSession, client: Client):
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client