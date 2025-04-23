from pydantic import EmailStr
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime, timezone

# Modelo de Stage
class StageBase(SQLModel):
    stage_name: str = Field(max_length=50, unique=True, nullable=False)


class Stage(StageBase, table=True):
    stage_id: Optional[int] = Field(default=None, primary_key=True)
    process_stages: list["ProcessStage"] = Relationship(back_populates="stage")


class StageCreate(StageBase):
    pass

# Modelos para la tabla Jobs
class JobBase(SQLModel):
    job_code: str = Field(max_length=50, unique=True, nullable=False)
    status: bool = Field(default=False, nullable=False)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class Job(JobBase, table=True):
    job_id: Optional[int] = Field(default=None, primary_key=True)
    items: list["Item"] = Relationship(back_populates="job")
    product_id: int = Field(foreign_key="product.product_id", nullable=False)
    product: "Product" = Relationship(back_populates="jobs")
    defect_records: list["DefectRecord"] = Relationship(back_populates="job")

class JobCreate(JobBase):
    client_id: int


class JobUpdate(SQLModel):
    pass

class JobResponse(JobBase):
    job_id: Optional[int] | None = None

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
    process_id: int = Field(foreign_key="process.process_id")

    process: "Process" =  Relationship(back_populates="items")


    @property
    def stage_ids(self) -> list[str]:
        """
        Devuelve una lista ordenada de nombres de stages para el proceso asociado con este Item.
        
        Returns:
            List[str]: Lista de nombres de stages ordenados según su orden en el proceso.
        """
        # El proceso está ya vinculado al Item a través de process_id
        # Ordenamos los stages por su orden en el proceso
        ordered_stage_ids = [
            ps.stage.stage_id 
            for ps in sorted(
                self.process.process_stages, 
                key=lambda ps: ps.order
            )
        ]
        return ordered_stage_ids

    @property
    def stage_names(self) -> list[str]:
        """
        Devuelve una lista ordenada de nombres de stages para el proceso asociado con este Item.
        
        Returns:
            List[str]: Lista de nombres de stages ordenados según su orden en el proceso.
        """
        # El proceso está ya vinculado al Item a través de process_id
        # Ordenamos los stages por su orden en el proceso
        ordered_stage_names = [
            ps.stage.stage_name 
            for ps in sorted(
                self.process.process_stages, 
                key=lambda ps: ps.order
            )
        ]
        return ordered_stage_names
    

class ItemCreate(ItemBase):
    job_id: int


class ItemUpdate(ItemBase):
    pass


# Modelos para la tabla Objects
class ObjectBase(SQLModel):
    current_stage: int = Field(foreign_key="stage.stage_id", default=1)
    rework: int = Field(default=0)
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
    objects: list[ObjectDetails]


# Tabla intermedia ProcessStage
class ProcessStage(SQLModel, table=True):
    __tablename__ = "process_stage"
    id: Optional[int] = Field(default=None, primary_key=True)
    process_id: int = Field(foreign_key="process.process_id", nullable=False)
    stage_id: int = Field(foreign_key="stage.stage_id", nullable=False)
    order: int = Field(nullable=False)  # Orden dentro del proceso

    process: "Process" = Relationship(back_populates="process_stages")
    stage: "Stage" = Relationship(back_populates="process_stages")
    

# Modelo de Process
class ProcessBase(SQLModel):
    process_name: str = Field(max_length=50, unique=True, nullable=False)


class Process(ProcessBase, table=True):
    process_id: Optional[int] = Field(default=None, primary_key=True)
    process_stages: list[ProcessStage] = Relationship(back_populates="process")
    items: list["Item"] = Relationship(back_populates="process")  # Relación con Item


class ProcessCreate(ProcessBase):
    pass


class ProcessUpdate(ProcessBase):
    pass

class ProcessResponse(ProcessBase):
    process_id: int
    process_name: str

class ItemStageStatus(SQLModel):
    item_name: str
    item_ocr: str
    ratio :str
    status: bool

class StageStatus(SQLModel):
    stage_name: str
    items: list[ItemStageStatus]

class JobStatus(SQLModel):
    job_code: str
    stages: list[StageStatus]


# --- Product ---
class ProductBase(SQLModel):
    product_name: str = Field(max_length=255, nullable = False)

class Product(ProductBase, table = True):
    product_id: Optional[int] = Field(default = None, primary_key = True)
    defect_records: list["DefectRecord"] = Relationship(back_populates= "product")
    jobs: list["Job"] = Relationship(back_populates="product")

class ProductCreate(ProductBase):
    pass

class PublicProduct(ProductBase):
    product_id: int

# --- Issue ---
class IssueBase(SQLModel):
    issue_description: str = Field(max_length=255, nullable=False)

class Issue(IssueBase, table=True):
    issue_id: Optional[int] = Field(default=None, primary_key=True)
    process_id: int = Field(foreign_key="process.process_id", nullable=False)
    defect_records: list["DefectRecord"] = Relationship(back_populates="issue")

class IssueCreate(IssueBase):
    process_id: int

class IssueUpdate(IssueBase):
    process_id: Optional[int]  # Optional if you want to allow changing the process association

class IssueResponse(IssueBase):
    issue_id: int
    process_id: int  # Include the process association in the response


# --- Status ---
class StatusBase(SQLModel):
    status_name: str = Field(max_length=50, unique=True, nullable=False)

class Status(StatusBase, table=True):
    status_id: Optional[int] = Field(default=None, primary_key=True)
    defect_records: list["DefectRecord"] = Relationship(back_populates="status")

class StatusCreate(StatusBase):
    pass

class StatusResponse(StatusBase):
    pass

class PublicStatus(SQLModel):
    status_name: str 

# --- Correction Process ---
class CorrectionProcessBase(SQLModel):
    correction_process_description: str = Field(max_length=255, nullable=False)

class CorrectionProcess(CorrectionProcessBase, table=True):
    __tablename__ = "correction_process"
    correction_process_id: Optional[int] = Field(default=None, primary_key=True)
    defect_records: list["DefectRecord"] = Relationship(back_populates="correction_process")

class CorrectionProcessCreate(CorrectionProcessBase):
    pass

class CorrectionProcessUpdate(CorrectionProcessBase):
    pass

class CorrectionProcessResponse(CorrectionProcessBase):
    correction_process_id: int


# --- Image Type ---
class ImageTypeBase(SQLModel):
    type_name: str = Field(max_length=50, unique=True, nullable=False)

class ImageType(ImageTypeBase, table=True):
    __tablename__ = "image_type"
    image_type_id: Optional[int] = Field(default=None, primary_key=True)
    defect_images: list["DefectImage"] = Relationship(back_populates="image_type")

class ImageTypeCreate(ImageTypeBase):
    pass

class ImageTypePublic(ImageTypeBase):
    pass

#==================================#
# --- Defect Record ---
#==================================#

class DefectRecordBase(SQLModel):
    product_id: int = Field(foreign_key="product.product_id")
    job_id: int = Field(foreign_key="job.job_id")
    inspector_user_id: int = Field(foreign_key="user.user_id")
    issue_by_user_id: int = Field(foreign_key="user.user_id")
    issue_id: int = Field(foreign_key="issue.issue_id")
    correction_process_id: int = Field(foreign_key="correction_process.correction_process_id")
    status_id: int = Field(foreign_key="status.status_id")
    date_closed: Optional[datetime] = Field(default=None)
    date_opened: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DefectRecord(DefectRecordBase, table=True):
    __tablename__ = "defect_record"
    defect_record_id: int = Field(default=None, primary_key=True)
    # Relaciones
    product: "Product" = Relationship(back_populates="defect_records")
    job: "Job" = Relationship(back_populates="defect_records")
    inspector: "User" = Relationship(back_populates="inspected_defects",sa_relationship_kwargs={"foreign_keys": "DefectRecord.inspector_user_id"})
    issue_by_user: "User" = Relationship(back_populates="user_defects",sa_relationship_kwargs={"foreign_keys": "DefectRecord.issue_by_user_id"})
    issue: "Issue" = Relationship(back_populates="defect_records")
    correction_process: "CorrectionProcess" = Relationship(back_populates="defect_records")
    status: "Status" = Relationship(back_populates="defect_records")
    images: list["DefectImage"] = Relationship(back_populates="defect_record")
    
    
class DefectRecordCreate(DefectRecordBase):
    pass



class DefectRecordUpdate(SQLModel):
    date_closed: Optional[datetime] = None
    product_id: Optional[int] = None
    job_id: Optional[int] = None
    process_id: Optional[int] = None
    inspector_user_id: Optional[int] = None
    issue_by_user_id: Optional[int] = None
    issue_id: Optional[int] = None
    correction_process_id: Optional[int] = None
    status_id: Optional[int] = None
    description: Optional[str] = None
    status: "Status" = Relationship(back_populates="defect_records")
    images: list["DefectImage"] = Relationship(back_populates="defect_record") 

class DefectRecordRead(DefectRecordBase):
    defect_record_id: int
    date_opened: datetime
    date_closed: Optional[datetime]

class DefectRecordResponse(SQLModel):
    defect_record_id: int
    job_code: str
    product: str
    inspectBy: str
    issueBy: str
    issue: str
    todo: str
    status: str
    process: str
    date_opened: datetime
    date_closed: Optional[datetime]




# class DefectRecordBase(SQLModel):
#     product_id: int = Field(foreign_key="product.product_id")
#     job_id: int = Field(foreign_key="job.job_id")
#     inspector_user_id: int = Field(foreign_key="user.user_id")
#     issue_by_user_id: int = Field(foreign_key="user.user_id")
#     issue_id: int = Field(foreign_key="issue.issue_id")
#     correction_process_id: int = Field(foreign_key="correction_process.correction_process_id")
#     status_id: int = Field(foreign_key="status.status_id")
#     date_closed: Optional[datetime] = Field(default=None)
#     date_opened: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    #agregar imagenes después

# class Status(str, Enum):
#     OK = "ok"
#     PENDING = "pending"
#     ERROR = "error"

#==================================#
# --- Defect Image ---
#==================================#
class DefectImageBase(SQLModel):
    image_url: str = Field(max_length=255, nullable=False)

class DefectImage(DefectImageBase, table=True):
    __tablename__ = "defect_image"
    defect_image_id: Optional[int] = Field(default=None, primary_key=True)
    defect_record_id: int = Field(foreign_key="defect_record.defect_record_id")
    image_type_id: int = Field(foreign_key="image_type.image_type_id")
    
    # Relaciones
    defect_record: DefectRecord = Relationship(back_populates="images")
    image_type: ImageType = Relationship(back_populates="defect_images")

class DefectImageCreate(DefectImageBase):
    defect_record_id: int
    image_type_id: int

class responseDefectImage(DefectImageBase):
    type_name: str
    
    @classmethod
    def from_orm(cls, defect_image: DefectImage):
        return cls(
            image_url=defect_image.image_url,
            type_name=defect_image.image_type.type_name
        )
    
class PublicDefectImage(DefectImageBase):
    image_type: ImageTypePublic | None = None


#==================================#
# --- Roles ---
#==================================#

class BaseRole(SQLModel):
    role_name: str = Field(unique=True)

class CreateRole(BaseRole):
    pass

class Role(BaseRole, table=True):
    role_id: Optional[int] = Field(default=None, primary_key=True)
    users: list["User"] = Relationship(back_populates="role")

#==================================#
# --- Tokens ---
#==================================#

class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: Optional[str] = None

#==================================#
# --- Users ---
#==================================#


class BaseUser(SQLModel):
    employee_number: int = Field(unique=True, nullable=False)
    username: str = Field(max_length=50, unique=True, nullable=False)
    email: str = Field(max_length=255, nullable=False)
    first_name: str = Field(max_length=50)
    middle_name: Optional[str] = Field(max_length=50, default=None)
    first_surname: str = Field(max_length=50)
    second_surname: Optional[str] = Field(max_length=50, default=None)

class CreateUser(BaseUser):
    password: str = Field(nullable=False)
    role_name: str = Field(nullable=False)

class User(BaseUser, table=True):
    __tablename__ = "user"
    user_id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(max_length=255, nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    role_id: int = Field(foreign_key="role.role_id", nullable=False)
    role: Role = Relationship(back_populates="users")

    # Relaciones con DefectRecord
    inspected_defects: list["DefectRecord"] = Relationship(
        back_populates="inspector",
        sa_relationship_kwargs={"foreign_keys": "DefectRecord.inspector_user_id"}
    )
    user_defects: list["DefectRecord"] = Relationship(
        back_populates="issue_by_user",
        sa_relationship_kwargs={"foreign_keys": "DefectRecord.issue_by_user_id"}
    )

    def update_timestamps(self):
        self.updated_at = datetime.now(timezone.utc)



class ResponseUser(SQLModel):
    user_id: int
    employee_number: int
    username: str
    email: EmailStr
    middle_name: Optional[str] = Field(max_length=50, default=None)
    first_surname: str = Field(max_length=50)
    second_surname: Optional[str] = Field(max_length=50, default=None)
    role: Role
    is_active: bool
    created_at: datetime

class UpdateUserRequest(SQLModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    first_surname: Optional[str] = None
    password: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None
    

# Modelos para el flujo
class ForgetPasswordRequest(SQLModel):
    email: str = Field(nullable=False)

class ResetPasswordRequest(SQLModel):
    token: str = Field(nullable=False)
    new_password: str = Field(nullable=False)
    confirm_password: str = Field(nullable=False)


class CompleteDefectRecordResponse(DefectRecordBase):

    product: ProductBase | None = None
    status: StatusBase | None = None
    images: list[PublicDefectImage]  | None = None
    inspector: ResponseUser | None = None
    issue_by_user: ResponseUser | None = None