from sqlmodel import SQLModel, Field
from typing import Optional


# Modelo Process_Stages
class ProcessStageBase(SQLModel):
    stage_order: int

class ProcessStage(ProcessStageBase, table=True):
    process_id: Optional[int] = Field(default=None, primary_key=True)

class ProcessStageCreate(ProcessStageBase):
    pass

class ProcessStageUpdate(ProcessStageBase):
    pass