from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from db import SessionDep
from models import Job, Object, Item, Stage, JobObjectsResponse, ObjectDetails
from typing import List, Dict

# Definimos el router
router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

@router.get("/{job_code}/objects", response_model=JobObjectsResponse)
def get_objects_by_job(job_code: str, session: SessionDep):
    # Verificar si el Job existe
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"El Job con código '{job_code}' no existe.")

    # Obtener todos los Items relacionados con el Job
    items = session.exec(select(Item).where(Item.job_id == job.job_id)).all()

    objects_details = []

    for item in items:
        # Obtener todos los Objects relacionados con el Item
        objects = session.exec(select(Object).where(Object.item_id == item.item_id)).all()
        
        # Agrupar los objetos por etapa
        stages_count = {}
        for obj in objects:
            stage = session.exec(select(Stage).where(Stage.stage_id == obj.current_stage)).first()
            stage_name = stage.stage_name if stage else "Unknown"
            if stage_name not in stages_count:
                stages_count[stage_name] = 0
            stages_count[stage_name] += 1

        # Añadir los detalles de los objetos por etapa
        for stage_name, count in stages_count.items():
            objects_details.append(ObjectDetails(
                item_name=item.item_name,
                stage_name=stage_name,
                count=count
            ))

    return JobObjectsResponse(
        job_code=job.job_code,
        objects=objects_details
    )
