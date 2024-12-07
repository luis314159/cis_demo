from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from db.connection import get_session
from models.client import Client

router = APIRouter()

@router.get("/")
async def get_clients(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Client))
    clients = result.scalars().all()
    return clients

@router.post("/")
async def create_client(client: Client, session: AsyncSession = Depends(get_session)):
    session.add(client)
    await session.commit()
    await session.refresh(client)
    return client
