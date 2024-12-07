from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime


# Modelo Scraps
class ScrapBase(SQLModel):
    scrapped_date: Optional[datetime] = Field(default=None)

class Scrap(ScrapBase, table=True):
    scrapped_id: Optional[int] = Field(default=None, primary_key=True)
    scrapped_object: Optional[int] = Field(foreign_key="object.object_id")
    authorized_by: Optional[int] = Field(foreign_key="user.user_id")
    scrapped_by: int = Field(foreign_key="user.user_id")

class ScrapCreate(ScrapBase):
    scrapped_object: Optional[int]
    authorized_by: Optional[int]
    scrapped_by: int

class ScrapUpdate(ScrapBase):
    pass
