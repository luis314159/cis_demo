from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime, timezone


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
    process_id: int = Field(foreign_key="process.process_id")

    process: "Process" =  Relationship(back_populates="items")

    # @property
    # def stages(self) -> list["Stage"]:
    #     """
    #     Devuelve una lista ordenada de diccionarios representando los stages
    #     para el proceso asociado con este Item.
        
    #     Returns:
    #         List[Dict]: Lista de stages ordenados como diccionarios.
    #     """
    #     return [
    #         {
    #             "stage_id": ps.stage.stage_id,
    #             "stage_name": ps.stage.stage_name
    #         }
    #         for ps in sorted(
    #             self.process.process_stages, 
    #             key=lambda ps: ps.order
    #         )
    #     ]

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


# class ItemStageStatus(SQLModel):
#     item_name: str
#     ocr : str
#     fraction: str #str(f"{completed}/{total})
#     status: bool

# class ItemStageStatus(SQLModel):
#     item_name: str
#     completed: int
#     pending :int
#      #str(f"{completed}/{total})


class ItemStageStatus(SQLModel):
    item_name: str
    # completed: int
    # pending :int

    item_ocr: str
    ratio :str
    status: bool

class StageStatus(SQLModel):
    stage_name: str
    items: List[ItemStageStatus]

class JobStatus(SQLModel):
    job_code: str
    stages: List[StageStatus]

