from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from job import Job


# Enumeraciones
class JobStatusEnum(bool, Enum):
    ACTIVE = True
    INACTIVE = False


# Modelos para la tabla Clients
class ClientBase(SQLModel):
    client_name: str = Field(max_length=50, nullable=False)
    phone: Optional[str] = Field(max_length=15)
    rfc: Optional[str] = Field(max_length=13)
    CP: Optional[str] = Field(max_length=5)
    address: Optional[str] = Field(max_length=50)


class Client(ClientBase, table=True):
    client_id: Optional[int] = Field(default=None, primary_key=True)
    jobs: List["Job"] = Relationship(back_populates="client")


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


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


# Modelos para la tabla Materials
class MaterialBase(SQLModel):
    material_name: str = Field(max_length=50, unique=True, nullable=False)


class Material(MaterialBase, table=True):
    material_id: Optional[int] = Field(default=None, primary_key=True)


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(MaterialBase):
    pass


# Modelos para la tabla Stages
class StageBase(SQLModel):
    stage_name: str = Field(max_length=20, unique=True, nullable=False)


class Stage(StageBase, table=True):
    stage_id: Optional[int] = Field(default=None, primary_key=True)


class StageCreate(StageBase):
    pass


class StageUpdate(StageBase):
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


# Modelos para la tabla Process_Stages
class ProcessStageBase(SQLModel):
    stage_order: int = Field(nullable=False)


class ProcessStage(ProcessStageBase, table=True):
    process_id: Optional[int] = Field(default=None, primary_key=True)


class ProcessStageCreate(ProcessStageBase):
    pass


class ProcessStageUpdate(ProcessStageBase):
    pass


# Modelos para la tabla Users
class RoleBase(SQLModel):
    role: str = Field(max_length=20, nullable=False)


class Role(RoleBase, table=True):
    role_id: Optional[int] = Field(default=None, primary_key=True)


class UserBase(SQLModel):
    first_name: str = Field(max_length=20, nullable=False)
    last_name: str = Field(max_length=20, nullable=False)
    email: EmailStr = Field(nullable=False)
    password_hash: str = Field(max_length=255, nullable=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)


class User(UserBase, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="role.role_id", nullable=False)
    role: Role = Relationship()


class UserCreate(UserBase):
    role_id: int


class UserUpdate(UserBase):
    pass


# Modelo Process_Stages
class ProcessStageBase(SQLModel):
    stage_order: int

class ProcessStage(ProcessStageBase, table=True):
    process_id: Optional[int] = Field(default=None, primary_key=True)

class ProcessStageCreate(ProcessStageBase):
    pass

class ProcessStageUpdate(ProcessStageBase):
    pass


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
