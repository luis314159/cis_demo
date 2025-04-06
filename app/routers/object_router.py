from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel import select
from db import SessionDep
from models import Job, Object, Item, Stage, JobObjectsResponse, ObjectDetails
from typing import List, Dict

# Definimos el router
router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

@router.get("/{job_code}/objects", response_model=JobObjectsResponse,
        summary="Get job objects distribution by stage",
        response_description="Returns object count grouped by item and stage",
        tags=["Jobs"],
        responses={
            200: {"description": "Successfully retrieved job objects distribution"},
            404: {"description": "Job not found"},
        },
    )
def get_objects_by_job(job_code: str, session: SessionDep):
    """
    ## Endpoint to get object distribution by processing stage for a job

    Retrieves detailed information about all objects associated with a job,
    grouped by item and their current processing stage.

    ### Arguments:
    - **job_code** (str): Unique identifier code for the job

    ### Returns:
    - **JobObjectsResponse**:
        - job_code: Original job code
        - objects: List of object groups containing:
            - item_name: Name of the parent item
            - stage_name: Current processing stage name
            - count: Number of objects in this stage

    ### Raises:
    - `HTTPException`:
        - 404: If specified job doesn't exist

    ### Example Usage:
    ```http
    GET /jobs/JOB-1234/objects

    Response:
    {
        "job_code": "JOB-1234",
        "objects": [
            {
                "item_name": "Steel Beam",
                "stage_name": "Cutting",
                "count": 15
            },
            {
                "item_name": "Steel Beam",
                "stage_name": "Welding",
                "count": 8
            },
            {
                "item_name": "Support Bracket",
                "stage_name": "Cutting",
                "count": 12
            }
        ]
    }
    ```

    ### Workflow:
    1. Validate job existence using provided job_code
    2. Retrieve all items associated with the job
    3. For each item:
        - Get all related objects
        - Group objects by their current processing stage
        - Count objects per stage
    4. Return aggregated results with stage names and counts
    """
    # Verificar si el Job existe
    job = session.exec(select(Job).where(Job.job_code == job_code)).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El Job con código '{job_code}' no existe.")

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


