from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


# Modelo Reworks
class ReworkBase(SQLModel):
    rework_date: Optional[datetime] = Field(default=None)

class Rework(ReworkBase, table=True):
    rework_id: Optional[int] = Field(default=None, primary_key=True)
    item_id: Optional[int] = Field(foreign_key="item.item_id")
    rework_allowed: int = Field(foreign_key="user.user_id")

class ReworkCreate(ReworkBase):
    item_id: Optional[int]
    rework_allowed: int

class ReworkUpdate(ReworkBase):
    pass
