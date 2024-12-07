from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from .job import Job
from .material import Material


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
    ocr: str = Field(max_length=255, nullable=False)


class Item(ItemBase, table=True):
    item_id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.job_id", nullable=False)
    material_id: int = Field(foreign_key="material.material_id", nullable=False)
    job: Job = Relationship(back_populates="items")
    material: Material = Relationship()


class ItemCreate(ItemBase):
    job_id: int
    material_id: int


class ItemUpdate(ItemBase):
    pass
