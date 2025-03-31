from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime, timezone
from models import User
# Modelo de Stage
class StageBase(SQLModel):
    stage_name: str = Field(max_length=50, unique=True, nullable=False)


class Stage(StageBase, table=True):
    stage_id: Optional[int] = Field(default=None, primary_key=True)
    process_stages: List["ProcessStage"] = Relationship(back_populates="stage")


class StageCreate(StageBase):
    pass

# Modelos para la tabla Jobs
class JobBase(SQLModel):
    job_code: str = Field(max_length=50, unique=True, nullable=False)
    status: bool = Field(default=False, nullable=False)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class JobCreate(JobBase):
    product_id: int = Field(foreign_key="product.product_id", nullable=False)
    product: "Product" = Relationship()

class Job(JobCreate, table=True):
    job_id: Optional[int] = Field(default=None, primary_key=True)
    items: list["Item"] = Relationship(back_populates="job")



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
    process_id: int = Field(foreign_key="process.process_id")

    process: "Process" =  Relationship(back_populates="items")


    @property
    def stage_ids(self) -> List[str]:
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
    def stage_names(self) -> List[str]:
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
    objects: List[ObjectDetails]


# Tabla intermedia ProcessStage
class ProcessStage(SQLModel, table=True):
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
    process_stages: List[ProcessStage] = Relationship(back_populates="process")
    items: List["Item"] = Relationship(back_populates="process")  # Relación con Item


class ProcessCreate(ProcessBase):
    pass


class ProcessUpdate(ProcessBase):
    pass


class ItemStageStatus(SQLModel):
    item_name: str
    item_ocr: str
    ratio :str
    status: bool

class StageStatus(SQLModel):
    stage_name: str
    items: List[ItemStageStatus]

class JobStatus(SQLModel):
    job_code: str
    stages: List[StageStatus]

# --- Product ---
class ProductBase(SQLModel):
    product_name: str = Field(max_length=255, nullable = False)

class Product(ProductBase, table = True):
    product_id: Optional[int] = Field(default = None, primary_key = True)
    defect_records: List["DefectRecord"] = Relationship(back_populates= "product")
    Job = List["Job"] = Relationship(back_populates="product")

class ProductCreate(ProductBase):
    pass

# --- Issue ---
class IssueBase(SQLModel):
    issue_description: str = Field(max_length=255, nullable=False)

class Issue(IssueBase, table=True):
    issue_id: Optional[int] = Field(default=None, primary_key=True)
    defect_records: List["DefectRecord"] = Relationship(back_populates="issue")

class IssueCreate(IssueBase):
    pass

# --- Status ---
class StatusBase(SQLModel):
    status_name: str = Field(max_length=50, unique=True, nullable=False)

class Status(StatusBase, table=True):
    status_id: Optional[int] = Field(default=None, primary_key=True)
    defect_records: List["DefectRecord"] = Relationship(back_populates="status")

class StatusCreate(StatusBase):
    pass

# --- Correction Process ---
class CorrectionProcessBase(SQLModel):
    correction_process_description: str = Field(max_length=255, nullable=False)

class CorrectionProcess(CorrectionProcessBase, table=True):
    correction_process_id: Optional[int] = Field(default=None, primary_key=True)
    defect_records: List["DefectRecord"] = Relationship(back_populates="correction_process")

class CorrectionProcessCreate(CorrectionProcessBase):
    pass

# --- Image Type ---
class ImageTypeBase(SQLModel):
    type_name: str = Field(max_length=50, unique=True, nullable=False)

class ImageType(ImageTypeBase, table=True):
    image_type_id: Optional[int] = Field(default=None, primary_key=True)
    defect_images: List["DefectImage"] = Relationship(back_populates="image_type")

class ImageTypeCreate(ImageTypeBase):
    pass

# --- Role ---
class RoleBase(SQLModel):
    role_name: str = Field(max_length=50, unique=True, nullable=False)

class Role(RoleBase, table=True):
    role_id: Optional[int] = Field(default=None, primary_key=True)
    users: List["User"] = Relationship(back_populates="role")

class RoleCreate(RoleBase):
    pass


# --- Defect Record ---
class DefectRecordBase(SQLModel):
    date_opened: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    date_closed: Optional[datetime] = Field(default=None)

class DefectRecord(DefectRecordBase, table=True):
    defect_record_id: Optional[int] = Field(default=None, primary_key=True)
    
    # Claves foráneas
    product_id: int = Field(foreign_key="product.product_id")
    job_id: int = Field(foreign_key="job.job_id")
    process_id: int = Field(foreign_key="process.process_id")
    inspector_user_id: int = Field(foreign_key="user.user_id")
    family_user_id: int = Field(foreign_key="user.user_id")
    issue_id: int = Field(foreign_key="issue.issue_id")
    correction_process_id: int = Field(foreign_key="correctionprocess.correction_process_id")
    status_id: int = Field(foreign_key="status.status_id")
    
    # Relaciones
    product: Product = Relationship(back_populates="defect_records")
    job: Job = Relationship()
    process: Process = Relationship()
    inspector: User = Relationship(
        back_populates="inspected_defects",
        sa_relationship_kwargs={"foreign_keys": "DefectRecord.inspector_user_id"}
    )
    family_user: User = Relationship(
        back_populates="family_defects",
        sa_relationship_kwargs={"foreign_keys": "DefectRecord.family_user_id"}
    )
    issue: Issue = Relationship(back_populates="defect_records")
    correction_process: CorrectionProcess = Relationship(back_populates="defect_records")
    status: Status = Relationship(back_populates="defect_records")
    images: List["DefectImage"] = Relationship(back_populates="defect_record")

class DefectRecordCreate(DefectRecordBase):
    product_id: int
    job_id: int
    process_id: int
    inspector_user_id: int
    family_user_id: int
    issue_id: int
    correction_process_id: int
    status_id: int

    # --- Defect Image ---
class DefectImageBase(SQLModel):
    image_url: str = Field(max_length=255, nullable=False)

class DefectImage(DefectImageBase, table=True):
    image_id: Optional[int] = Field(default=None, primary_key=True)
    defect_record_id: int = Field(foreign_key="defectrecord.defect_record_id")
    image_type_id: int = Field(foreign_key="imagetype.image_type_id")
    
    # Relaciones
    defect_record: DefectRecord = Relationship(back_populates="images")
    image_type: ImageType = Relationship(back_populates="defect_images")

class DefectImageCreate(DefectImageBase):
    defect_record_id: int
    image_type_id: int

