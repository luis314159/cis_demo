from sqlmodel import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from contextlib import asynccontextmanager
from decouple import config

from models import item, object  # Para manejar variables de entorno

# Cargar la URL de conexión desde el archivo .env
DATABASE_URL = config("DATABASE_URL", default="postgresql+asyncpg://postgres:password@localhost:5432/db_name")
DEBUG = config("DEBUG", default=False, cast=bool)
SECRET_KEY = config("SECRET_KEY", default="default_key")

# Crear el motor de base de datos asincrónico
# engine: AsyncEngine = create_async_engine(DATABASE_URL)#, echo=True)
engine = create_engine(DATABASE_URL)
# Inicializar las tablas en la base de datos
async def init_db():
    """Inicializa la base de datos creando todas las tablas definidas en SQLModel."""
    from sqlmodel import SQLModel
    from models import client, job, material, stage, role, user, process_Stage, rework, role, user

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Proveer un manejador de sesión de base de datos
@asynccontextmanager
async def get_session() -> AsyncSession:
    """Provee una sesión asincrónica para interactuar con la base de datos."""
    async_session = AsyncSession(engine)
    try:
        yield async_session
    finally:
        await async_session.close()
