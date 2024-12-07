from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


# Modelo Object_Process_Stages
class ObjectProcessStageBase(SQLModel):
    completed: bool = Field(default=False)
    move_in: Optional[datetime] = Field(default=None)
    move_out: Optional[datetime] = Field(default=None)

class ObjectProcessStage(ObjectProcessStageBase, table=True):
    process_stage_id: Optional[int] = Field(default=None, primary_key=True)
    object_id: int = Field(foreign_key="object.object_id")
    stage_id: int = Field(foreign_key="stage.stage_id")
    process_id: int = Field(foreign_key="processstage.process_id")
    user_id: int = Field(foreign_key="user.user_id")

class ObjectProcessStageCreate(ObjectProcessStageBase):
    object_id: int
    stage_id: int
    process_id: int
    user_id: int

class ObjectProcessStageUpdate(ObjectProcessStageBase):
    pass