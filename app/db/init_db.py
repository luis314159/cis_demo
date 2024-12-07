from sqlmodel import SQLModel
from db.connection import engine

# async def init_db():
#     async with engine.begin() as conn:
#         conn.run_sync(SQLModel.metadata.create_all)
#         await conn.run_sync(SQLModel.metadata.create_all)
        

def init_db():
    with engine.begin() as conn:
        SQLModel.metadata.create_all(bind=conn)