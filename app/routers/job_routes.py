from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_session
from db import SessionDep
from models import Job
from sqlmodel import select
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_session
from services.job_services import process_csv_and_save_items


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

@router.get("/all_jobs", response_model=list[Job])
def get_item(session: SessionDep):
    """
    Devuelve una lista de todos los Jobs_codes existentes.
    """
    return session.exec(select(Job)).all()


@router.get("/job_available/{job_code}", response_model=bool)
def check_job_available(job_code: str, session: SessionDep):
    """
    Verifica si un job_code está disponible.
    Retorna True si el job_code no existe en la base de datos,
    False si ya está en uso.
    """
    # Buscar si existe un Job con el job_code dado
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    # Retornar True si no existe, False si ya está en uso
    return job is None


@router.get("/job_exists/{job_code}", response_model=bool)
def check_job_exists(job_code: str, session: SessionDep):
    """
    Verifica si un job_code existe.
    Retorna True si el job_code existe en la base de datos,
    False si no existe.
    """
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return True


@router.post("/upload_csv/")
async def upload_items_csv(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)):
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="El archivo debe ser un CSV")

    result = await process_csv_and_save_items(file, session)
    return {"detail": result}
