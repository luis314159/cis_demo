from fastapi import APIRouter
from sqlmodel import select
from db import SessionDep
from models import Job
from typing import List
from sqlmodel import SQLModel

# Crear un modelo de respuesta para listar Jobs
class JobList(SQLModel):
    job_code: str

# Crear el router
router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

@router.get("/list", response_model=List[JobList])
def list_jobs(session: SessionDep):
    # Obtener todos los Jobs disponibles
    jobs = session.exec(select(Job)).all()

    # Transformar a la respuesta deseada
    job_list = [JobList(job_code=job.job_code) for job in jobs]

    return job_list
