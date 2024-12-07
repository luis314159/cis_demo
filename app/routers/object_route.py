from fastapi import APIRouter
from db import SessionDep
from models import Job
from sqlmodel import select
from fastapi import APIRouter
from models import Object
from fastapi import APIRouter, Depends, HTTPException
from db import SessionDep
from models import Job, Object
from sqlmodel import select
from models import ObjectResponse


router = APIRouter(
    prefix="/objects",
    tags=["Object"]
)
    
@router.get("/job_items/{job_code}", response_model=list[ObjectResponse])
def check_job_available(job_code: str, session: SessionDep):
    """
    Dado un job_code obtiene los objetos asociados, mostrando sus OCR y la cantidad de estos.
    """
    # Verificar si el Job con el código especificado existe
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Obtener los objetos asociados al job
    objects = session.exec(
        select(Object).where(Object.job_id == job.job_id)
    ).all()

    # Construir la respuesta
    return [{"ocr": obj.ocr, "cantidad": obj.cantidad} for obj in objects]