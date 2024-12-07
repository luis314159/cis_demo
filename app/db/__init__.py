from fastapi import FastAPI
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends
from decouple import config

# DATABASE_URL = config(
#     "DATABASE_URL",
#     default="postgresql+asyncpg://postgres:password@localhost:5432/db_name"
# )
DATABASE_URL = config(
    "DATABASE_URL",
    default="postgresql://postgres:password@localhost:5432/db_name"
)
DEBUG = config("DEBUG", default=False, cast=bool)
SECRET_KEY = config("SECRET_KEY", default="default_key")

engine = create_engine(DATABASE_URL) #, echo=True)

# Configurar la sesión asíncrona
def get_session():
    with Session(engine) as session:
        yield session


def create_all_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

SessionDep = Annotated[AsyncSession, Depends(get_session)]