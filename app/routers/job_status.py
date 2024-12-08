from fastapi import APIRouter, HTTPException
from sqlmodel import select
from db import SessionDep
from models import Job, Item, JobStatus, ProcessStage, StageStatus, ItemStageStatus, Object, Stage
from sqlmodel import SQLModel

# Crear un modelo de respuesta para listar Jobs
class JobList(SQLModel):
    job_code: str

# Crear el router
router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

@router.get("/{job_code}/status", response_model=JobStatus)
def get_job_status(job_code: str, session: SessionDep):
    """
    Endpoint para obtener el estado de los objetos de un Job.
    """
    # Verificar que el Job existe
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    job_id = session.exec(select(Job.job_id).where(Job.job_code == job_code)).first()
    if not job:
        raise HTTPException(status_code=404, detail="El Job no existe.")

    # Obtener todos los Items relacionados al Job
    items = session.exec(select(Item).where(Item.job_id == job_id)).all()
    if not items:
        raise HTTPException(status_code=404, detail="No se encontraron Items relacionados al Job.")

    # Diccionario para almacenar el progreso por estación
    progress_data = {}

    for item in items:
        # Obtener los objetos relacionados al Item
        objects = session.exec(select(Object).where(Object.item_id == item.item_id)).all()

        # Obtener los stages del proceso del Item, en orden
        process_stages = session.exec(
            select(ProcessStage, Stage)
            .join(Stage, Stage.stage_id == ProcessStage.stage_id)
            .where(ProcessStage.process_id == item.process_id)
            .order_by(ProcessStage.order)
        ).all()

        # Analizar cada estación
        for process_stage, stage in process_stages:
            stage_name = stage.stage_name
            if stage_name not in progress_data:
                progress_data[stage_name] = {}

            # Inicializar datos para el item en esta etapa
            if item.item_name not in progress_data[stage_name]:
                progress_data[stage_name][item.item_name] = {"completed": 0, "pending": 0}

            # Analizar cada objeto y determinar su estado en la etapa
            for obj in objects:
                if obj.current_stage >= process_stage.order:
                    progress_data[stage_name][item.item_name]["completed"] += 1
                else:
                    progress_data[stage_name][item.item_name]["pending"] += 1

    # Construir la respuesta
    stages = []
    for stage_name, items_data in progress_data.items():
        stages.append(
            StageStatus(
                stage_name=stage_name,
                items=[
                    ItemStageStatus(
                        item_name=item_name,
                        completed=data["completed"],
                        pending=data["pending"]
                    )
                    for item_name, data in items_data.items()
                ]
            )
        )

    return JobStatus(
        job_code=job.job_code,
        stages=stages
    )
