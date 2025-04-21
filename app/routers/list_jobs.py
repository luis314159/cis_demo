from fastapi import APIRouter, status
from sqlmodel import select
from db import SessionDep
from models import Job, Product, JobResponse
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
                status_code=status.HTTP_200_OK,
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

@router.get("/list-by-product/{product_name}", response_model=List[JobList],
                summary="List all jobs",
                response_description="Returns a list of all jobs",
                tags=["Jobs"],  # Agrupa en la sección "Jobs"
                status_code=status.HTTP_200_OK,
            )
def list_jobs(product_name: str, session: SessionDep):
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

    query = (
        select(Job)
        .join(Product, Job.product_id == Product.product_id)
        .where(Product.product_name == product_name)
    )

    # Obtener todos los Jobs disponibles
    results = session.exec(query).all()

    # Transformar a la respuesta deseada
    job_list = [JobList(job_code=job.job_code) for job in results]

    return job_list


@router.get("/list-by-product-info/{product_name}", response_model=list[JobResponse],
                summary="List all jobs",
                response_description="Returns a list of all jobs",
                tags=["Jobs"],  # Agrupa en la sección "Jobs"
                status_code=status.HTTP_200_OK,
            )
def list_jobs_info(product_name: str, session: SessionDep):
    """
    ## Endpoint to list all jobs

    This endpoint retrieves a list of all jobs available in the system.

    ### Returns:
    - **List[JobList]**: A list of all jobs, each containing the job code.

    ### Example Usage:
    ```http
    GET /jobs/list
    ```

    ### Workflow:
    1. Query the database to retrieve all jobs.
    2. Transform the job data into the desired response format.
    3. Return the list of jobs.

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
    """

    query = (
        select(Job)
        .join(Product, Job.product_id == Product.product_id)
        .where(Product.product_name == product_name)
    )

    # Obtener todos los Jobs disponibles
    results = session.exec(query).all()

    # Transformar a la respuesta deseada

    return results
