# Evitar importación circular
from __future__ import annotations
from datetime import date, datetime, timezone
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from pydantic import EmailStr, field_validator, FieldValidationInfo
from fastapi import UploadFile
from typing import Optional, TYPE_CHECKING

#if TYPE_CHECKING:

#    from .cis_models import Job, Object

# Modelos para la tabla DefectCode
class DefectCodeBase(SQLModel):
    code: int = Field(nullable=False)
    description: str = Field(max_length=255, nullable=False)


class DefectCode(DefectCodeBase, table=True):
    defect_code_id: Optional[int] = Field(default=None, primary_key=True)
    punch_lists: list["PunchList"] = Relationship(back_populates="defect_code")


class DefectCodeCreate(DefectCodeBase):
    pass


class DefectCodeUpdate(DefectCodeBase):
    pass


# Modelos para la tabla PunchList
class PunchListBase(SQLModel):
    description: str = Field(max_length=255, nullable=False)
    date_open: date = Field(default_factory=lambda: datetime.now(timezone.utc).date())
    inspected_by: str = Field(nullable=False)  # Número del inspector
    issue: str = Field(nullable=False)
    todolist: str = Field(nullable=False)  # Tareas a realizar
    by_when: date = Field(nullable=False)  # Fecha estimada
    date_close: Optional[date] = None
    status: str = Field(default="Open", nullable=False)  # Open, In Progress, Closed


class PunchList(PunchListBase, table=True):
    punch_list_id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.job_id", nullable=False)
    job: "Job" = Relationship(back_populates="punch_lists")
    object_id: int = Field(foreign_key="object.object_id", nullable=False)
    object: "Object" = Relationship(back_populates="punch_lists")
    defect_code_id: int = Field(foreign_key="defectcode.defect_code_id", nullable=False)
    defect_code: DefectCode = Relationship(back_populates="punch_lists")
    picture_before_repair: Optional[str] = None  # Ruta a la imagen
    picture_after_repair: Optional[str] = None  # Ruta a la imagen
    inspector_validation_image: Optional[str] = None  # Selfie de validación


class PunchListCreate(PunchListBase):
    job_id: int
    object_id: int
    defect_code_id: int
    picture_before_repair: Optional[UploadFile] = None


class PunchListUpdate(SQLModel):
    description: Optional[str] = None
    issue: Optional[str] = None
    todolist: Optional[str] = None
    by_when: Optional[date] = None
    date_close: Optional[date] = None
    status: Optional[str] = None
    picture_after_repair: Optional[UploadFile] = None
    inspector_validation_image: Optional[UploadFile] = None


class PunchListResponse(PunchListBase):
    punch_list_id: int
    job_id: int
    object_id: int
    defect_code_id: int
    picture_before_repair: Optional[str] = None
    picture_after_repair: Optional[str] = None
    inspector_validation_image: Optional[str] = None

PunchList.model_rebuild()