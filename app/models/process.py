from typing import Optional
from sqlmodel import Field, SQLModel



# Modelos para la tabla Stages
class ProcessBase(SQLModel):
    stage_name: str = Field(max_length=20, unique=True, nullable=False)


class Process(ProcessBase, table=True):
    stage_id: Optional[int] = Field(default=None, primary_key=True)


class ProcessCreate(ProcessBase):
    pass


class ProcessUpdate(ProcessBase):
    pass