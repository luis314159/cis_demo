from typing import Optional
from sqlmodel import Field, SQLModel



# Modelos para la tabla Stages
class StageBase(SQLModel):
    stage_name: str = Field(max_length=20, unique=True, nullable=False)


class Stage(StageBase, table=True):
    stage_id: Optional[int] = Field(default=None, primary_key=True)


class StageCreate(StageBase):
    pass


class StageUpdate(StageBase):
    pass