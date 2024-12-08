from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from typing import List, Optional
from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel


# Modelos para la tabla Jobs
class JobBase(SQLModel):
    job_code: str = Field(max_length=50, unique=True, nullable=False)
    status: bool = Field(default=False, nullable=False)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class Job(JobBase, table=True):
    job_id: Optional[int] = Field(default=None, primary_key=True)
    items: list["Item"] = Relationship(back_populates="job")


class JobCreate(JobBase):
    client_id: int


class JobUpdate(JobBase):
    pass


# Modelos para la tabla Items
class ItemBase(SQLModel):
    item_name: str = Field(max_length=255, nullable=False)
    espesor: float
    longitud: float
    ancho: float
    alto: float
    volumen: float
    area_superficial: float
    cantidad: int
    material: str = Field(default="Steel")
    ocr: str = Field(max_length=255, nullable=False)


class Item(ItemBase, table=True):
    item_id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.job_id", nullable=False)
    job: Job = Relationship(back_populates="items")
    # Renombrar la relación de "object" a "related_objects"
    related_objects: list["Object"] = Relationship(back_populates="item")



class ItemCreate(ItemBase):
    job_id: int


class ItemUpdate(ItemBase):
    pass


# Modelos para la tabla Stages
class StageBase(SQLModel):
    stage_name: str = Field(max_length=20, unique=True, nullable=False)


class Stage(StageBase, table=True):
    stage_id: Optional[int] = Field(default=None, primary_key=True)


class StageCreate(StageBase):
    pass


# Modelos para la tabla Objects
class ObjectBase(SQLModel):
    current_stage: int = Field(foreign_key="stage.stage_id", default=0)
    rework: int
    scrap: Optional[int]


class Object(ObjectBase, table=True):
    object_id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.item_id", nullable=False)
    item: Item = Relationship(back_populates="related_objects")

class ObjectCreate(ObjectBase):
    item_id: int


class ObjectUpdate(ObjectBase):
    pass


class ObjectDetails(SQLModel):
    item_name: str
    stage_name: str
    count: int

class JobObjectsResponse(SQLModel):
    job_code: str
    objects: List[ObjectDetails]
