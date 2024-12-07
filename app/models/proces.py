from sqlmodel import SQLModel, Field
from typing import Optional


# Modelo Process
class ProcessBase(SQLModel):
    stage_order: int

class Process(ProcessBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    process_id: int = Field(foreign_key="processstage.process_id")
    stage_id: int = Field(foreign_key="stage.stage_id")

class ProcessCreate(ProcessBase):
    process_id: int
    stage_id: int

class ProcessUpdate(ProcessBase):
    pass