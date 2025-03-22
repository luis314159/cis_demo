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

@router.get("/list", response_model=List[JobList],
                summary="List all jobs",
                response_description="Returns a list of all jobs",
                tags=["Jobs"],  # Agrupa en la sección "Jobs"
                responses={
                    200: {"description": "Successfully returned the list of jobs"},
                },
            )
def list_jobs(session: SessionDep):
    """
    ## Endpoint to list all jobs

    This endpoint retrieves a list of all jobs available in the system.

    ### Returns:
    - **List[JobList]**: A list of all jobs, each containing the job code.

    ### Example Usage:
    ```http
    GET /jobs/list

    Response:
    [
        {
            "job_code": "JOB123"
        },
        {
            "job_code": "JOB456"
        },
        ...
    ]
    ```

    ### Workflow:
    1. Query the database to retrieve all jobs.
    2. Transform the job data into the desired response format.
    3. Return the list of jobs.
    """
    # Obtener todos los Jobs disponibles
    jobs = session.exec(select(Job)).all()

    # Transformar a la respuesta deseada
    job_list = [JobList(job_code=job.job_code) for job in jobs]

    return job_list
