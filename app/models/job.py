from typing import List, Optional
from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel
from client import Client
from item import Item


# Modelos para la tabla Jobs
class JobBase(SQLModel):
    job_code: str = Field(max_length=50, unique=True, nullable=False)
    status: bool = Field(default=False, nullable=False)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)


class Job(JobBase, table=True):
    job_id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.client_id", nullable=False)
    client: Client = Relationship(back_populates="jobs")
    items: List["Item"] = Relationship(back_populates="job")


class JobCreate(JobBase):
    client_id: int


class JobUpdate(JobBase):
    pass

