from typing import List, Optional
from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel
from models.item import Item


# Modelos para la tabla Jobs
class JobBase(SQLModel):
    job_code: str = Field(max_length=50, unique=True, nullable=False)
    status: bool = Field(default=False, nullable=False)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class Job(JobBase, table=True):
    job_id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.client_id", nullable=False)
    items: List["Item"] = Relationship(back_populates="job")


class JobCreate(JobBase):
    client_id: int


class JobUpdate(JobBase):
    pass


# Modelos para la tabla Objects
class ObjectBase(SQLModel):
    current_stage: int = Field(foreign_key="stage.stage_id", nullable=False)
    rework: int
    scrap: Optional[int]


class Object(ObjectBase, table=True):
    object_id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.item_id", nullable=False)
    item: Item = Relationship()


class ObjectCreate(ObjectBase):
    item_id: int


class ObjectUpdate(ObjectBase):
    pass

